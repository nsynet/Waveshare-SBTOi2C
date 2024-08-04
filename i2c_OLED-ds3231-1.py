import time
import datetime
from ctypes import *

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

# I2C addresses for the DS3231 RTC and OLED display 128x64
RTC_ADDRESS = 0x68
OLED_ADDRESS = 0x3C  # Verify this address

class WaveshareI2C:
    def __init__(self, usb_dev=0):
        self.usb_id = usb_dev
        if ch347_dll.CH347OpenDevice(self.usb_id) != -1:
            print("Device Opened Successfully!")
            self.initialize_i2c()
        else:
            raise Exception("Device Open Failed!")

    def initialize_i2c(self):
        if not ch347_dll.CH347I2C_Set(self.usb_id, 0x20):  # Set I2C speed
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

    @staticmethod
    def bcd_to_dec(bcd):
        return (bcd // 16 * 10) + (bcd % 16)

    @staticmethod
    def dec_to_bcd(dec):
        return (dec // 10 * 16) + (dec % 10)

class OLED:
    def __init__(self, i2c, address=OLED_ADDRESS):
        self.i2c = i2c
        self.address = address
        self.initialize_display()

    def initialize_display(self):
        # Initialization sequence for the OLED display
        init_sequence = [
            0xAE,  # Display off
            0xD5, 0x80,  # Set display clock divide ratio/oscillator frequency
            0xA8, 0x1F,  # Set multiplex ratio (1 to 32)
            0xD3, 0x00,  # Set display offset
            0x40,  # Set start line address
            0x8D, 0x14,  # Enable charge pump
            0x20, 0x00,  # Set memory addressing mode
            0xA1,  # Set segment re-map 0 to 127
            0xC8,  # Set COM output scan direction
            0xDA, 0x02,  # Set COM pins hardware configuration
            0x81, 0x8F,  # Set contrast control
            0xD9, 0xF1,  # Set pre-charge period
            0xDB, 0x40,  # Set VCOMH deselect level
            0xA4,  # Entire display on, resume to RAM content display
            0xA6,  # Normal display mode
            0xAF,  # Display on
        ]
        for cmd in init_sequence:
            self.send_command(cmd)

    def send_command(self, command):
        self.i2c.write(self.address, 0x00, command)

    def clear_display(self):
        # Clear the display by writing zeros to the entire screen
        for i in range(4):  # 4 pages for 128x32
            self.send_command(0xB0 + i)  # Set page start address
            self.send_command(0x00)      # Set lower column start address
            self.send_command(0x10)      # Set higher column start address
            for j in range(128):         # 128 columns
                self.i2c.write(self.address, 0x40, 0x00)

    def draw_text(self, text, x, y):
        # Simple method to draw text at a given position
        self.send_command(0xB0 + y)  # Page number (0 to 3 for 128x32)
        self.send_command(0x00 + (x & 0x0F))  # Lower nibble of column start address
        self.send_command(0x10 + ((x >> 4) & 0x0F))  # Higher nibble of column start address
        # Example font data for drawing text
        font_data = {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x62, 0x51, 0x49, 0x49, 0x46],
            '3': [0x22, 0x41, 0x49, 0x49, 0x36],
            '4': [0x0F, 0x08, 0x08, 0x7F, 0x08],
            '5': [0x4F, 0x49, 0x49, 0x49, 0x31],
            '6': [0x3E, 0x49, 0x49, 0x49, 0x32],
            '7': [0x01, 0x01, 0x71, 0x0D, 0x03],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x26, 0x49, 0x49, 0x49, 0x3E],
            ':': [0x00, 0x36, 0x36, 0x00, 0x00],
            '/': [0x40, 0x30, 0x08, 0x06, 0x01],
            'M': [0x7F, 0x02, 0x04, 0x02, 0x7F],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'Y': [0x07, 0x08, 0x78, 0x08, 0x07]  # Corrected Y
        }
        
        for char in text:
            data = font_data.get(char, font_data[' '])
            for byte in data:
                self.i2c.write(self.address, 0x40, byte)

def main():
    try:
        i2c_interface = WaveshareI2C()
        rtc = DS3231(i2c_interface)
        oled = OLED(i2c_interface)

        prev_time_str = ""
        prev_date_str = ""
        prev_day_str = ""

        while True:
            now, day_of_week = rtc.read_time()
            date_str = now.strftime("%m/%d/%Y")
            time_str = now.strftime("%H:%M:%S")
            day_str = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][day_of_week - 1]

            # Update only if the content changes
            if time_str != prev_time_str:
                oled.draw_text(time_str, 0, 0)
                prev_time_str = time_str

            if day_str != prev_day_str:
                oled.draw_text(day_str, 0, 1)
                prev_day_str = day_str

            if date_str != prev_date_str:
                oled.draw_text(date_str, 0, 2)
                prev_date_str = date_str

            time.sleep(1)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'i2c_interface' in locals():
            i2c_interface.close_device()

if __name__ == "__main__":
    main()
