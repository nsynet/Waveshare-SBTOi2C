import time
import datetime
from ctypes import *
import tkinter as tk

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

# I2C address for the DS3231 RTC
RTC_ADDRESS = 0x68

# Initialize I2C with Waveshare
class WaveshareI2C:
    def __init__(self, usb_dev=0):
        self.usb_id = usb_dev
        if ch347_dll.CH347OpenDevice(self.usb_id) != -1:
            print("Device Opened Successfully!")
            self.initialize_i2c()
        else:
            raise Exception("Device Open Failed!")

    def initialize_i2c(self):
        if not ch347_dll.CH347I2C_Set(self.usb_id, 0x20):  # Set appropriate I2C speed
            raise Exception("Failed to initialize I2C")

    def close_device(self):
        ch347_dll.CH347CloseDevice(self.usb_id)
        print("Device Closed.")

    def write(self, addr, register, data):
        # Write to I2C device
        tcmd = (c_ubyte * 3)()
        ibuf = (c_ubyte * 1)()
        tcmd[0] = addr << 1
        tcmd[1] = register
        tcmd[2] = data
        result = ch347_dll.CH347StreamI2C(self.usb_id, 3, tcmd, 0, ibuf)
        if not result:
            raise Exception(f"Failed to write to address {hex(addr)}")

    def read(self, addr, register, length):
        # Read from I2C device
        tcmd = (c_ubyte * 2)()
        rbuf = (c_ubyte * length)()
        tcmd[0] = addr << 1
        tcmd[1] = register
        result = ch347_dll.CH347StreamI2C(self.usb_id, 2, tcmd, length, rbuf)
        if not result:
            raise Exception(f"Failed to read from address {hex(addr)}")
        return rbuf

class DS3231:
    def __init__(self, i2c, address=RTC_ADDRESS):
        self.i2c = i2c
        self.address = address

    def read_time(self):
        data = self.i2c.read(self.address, 0x00, 7)
        seconds = self.bcd_to_dec(data[0] & 0x7F)
        minutes = self.bcd_to_dec(data[1])
        hours = self.bcd_to_dec(data[2] & 0x3F)
        day_of_week = self.bcd_to_dec(data[3])
        day_of_month = self.bcd_to_dec(data[4])
        month = self.bcd_to_dec(data[5] & 0x1F)
        year = self.bcd_to_dec(data[6]) + 2000
        return datetime.datetime(year, month, day_of_month, hours, minutes, seconds), day_of_week

    def set_time(self, dt):
        data = [
            self.dec_to_bcd(dt.second),
            self.dec_to_bcd(dt.minute),
            self.dec_to_bcd(dt.hour),
            self.dec_to_bcd(dt.isoweekday() % 7 + 1),  # DS3231: Sunday = 1, ISO: Monday = 1
            self.dec_to_bcd(dt.day),
            self.dec_to_bcd(dt.month),
            self.dec_to_bcd(dt.year - 2000)
        ]
        for i, val in enumerate(data):
            self.i2c.write(self.address, i, val)
        print(f"RTC time set to {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    @staticmethod
    def bcd_to_dec(bcd):
        return (bcd // 16 * 10) + (bcd % 16)

    @staticmethod
    def dec_to_bcd(dec):
        return (dec // 10 * 16) + (dec % 10)

def day_of_week_str(day_of_week):
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    return days[(day_of_week - 1) % 7]

def update_display(label, rtc):
    current_time, day_of_week = rtc.read_time()
    time_str = current_time.strftime('%H:%M:%S')
    date_str = current_time.strftime('%m/%d/%Y')
    day_str = day_of_week_str(day_of_week)
    label.config(text=f"{time_str}\n{day_str}\n{date_str}")
    label.after(1000, update_display, label, rtc)  # Update every second

def main():
    try:
        i2c_interface = WaveshareI2C()
        rtc = DS3231(i2c_interface)

        # Check and synchronize the time
        current_time, rtc_day_of_week = rtc.read_time()
        system_time = datetime.datetime.now()
        system_day_of_week = system_time.isoweekday() % 7 + 1  # Convert ISO to DS3231 day format

        # Sync RTC if the difference is more than 15 seconds or the day of the week is incorrect
        if abs((system_time - current_time).total_seconds()) > 15 or rtc_day_of_week != system_day_of_week:
            print(f"RTC time is off by {abs(system_time - current_time).total_seconds()} seconds")
            print("Syncing RTC with system time and correcting day of the week")
            rtc.set_time(system_time)

        # Tkinter setup
        root = tk.Tk()
        root.title("RTC Time Display")
        label = tk.Label(root, font=("Arial", 24), justify="center")
        label.pack(padx=20, pady=20)

        # Start updating the display
        update_display(label, rtc)

        root.mainloop()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        i2c_interface.close_device()

if __name__ == "__main__":
    main()
