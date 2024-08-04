import time
from ctypes import *

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

class OLED:
    def __init__(self, usb_dev=0, i2c_addr=0x3C):  # Default I2C address for OLED
        self.usb_id = usb_dev
        self.dev_addr = i2c_addr

        # Open the USB device
        if ch347_dll.CH347OpenDevice(self.usb_id) != -1:
            print("USB CH347 Device Opened Successfully!")
            self.initialize_display()
        else:
            raise Exception("USB CH347 Open Failed!")

    def close_device(self):
        ch347_dll.CH347CloseDevice(self.usb_id)
        print("USB CH347 Device Closed.")

    def write_command(self, command):
        # Prepare the command buffer
        cmd = (c_byte * 3)()
        cmd[0] = self.dev_addr << 1  # I2C device address with write flag
        cmd[1] = 0x00  # Command mode
        cmd[2] = command  # Actual command

        # Perform the I2C write operation
        result = ch347_dll.CH347StreamI2C(self.usb_id, 3, cmd, 0, None)
        if result != 1:
            raise Exception(f"Failed to send command: {hex(command)}")

    def write_data(self, data):
        # Prepare data buffer
        data_packet = (c_byte * (len(data) + 2))()
        data_packet[0] = self.dev_addr << 1  # I2C device address with write flag
        data_packet[1] = 0x40  # Data mode

        for i in range(len(data)):
            data_packet[i + 2] = data[i]

        # Perform the I2C write operation
        result = ch347_dll.CH347StreamI2C(self.usb_id, len(data_packet), data_packet, 0, None)
        if result != 1:
            raise Exception("Failed to write data to OLED")

    def initialize_display(self):
        try:
            # Initialization sequence for a typical SSD1306 OLED
            init_sequence = [
                0xAE,  # Display OFF (sleep mode)
                0xD5,  # Set display clock divide ratio/oscillator frequency
                0x80,  # Set divide ratio
                0xA8,  # Set multiplex ratio(1 to 64)
                0x3F,  # 1/64 duty
                0xD3,  # Set display offset
                0x00,  # Not offset
                0x40,  # Set start line address
                0x8D,  # Charge pump setting
                0x14,  # Enable charge pump
                0x20,  # Memory addressing mode
                0x00,  # Horizontal addressing mode
                0xA1,  # Set segment re-map 0 to 127
                0xC8,  # Set COM output scan direction
                0xDA,  # Set COM pins hardware configuration
                0x12,  # COM pins
                0x81,  # Set contrast control
                0xCF,  # Contrast
                0xD9,  # Set pre-charge period
                0xF1,  # Pre-charge period
                0xDB,  # Set VCOMH deselect level
                0x40,  # VCOMH
                0xA4,  # Entire display ON
                0xA6,  # Set normal display
                0xAF   # Display ON
            ]

            for cmd in init_sequence:
                self.write_command(cmd)

            self.clear_display()

            print("OLED Initialized")
        except Exception as e:
            print(f"Initialization error: {e}")

    def clear_display(self):
        # Clear the screen by filling it with 0s (black)
        for page in range(8):  # SSD1306 has 8 pages
            self.write_command(0xB0 + page)  # Set page address
            self.write_command(0x00)         # Set lower column address
            self.write_command(0x10)         # Set higher column address
            self.write_data([0x00] * 128)    # Clear all 128 columns

    def display_number(self, number):
        # Convert the number to a string and then to a format suitable for the OLED
        font = {
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x42, 0x61, 0x51, 0x49, 0x46],
            '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
            '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
            '5': [0x27, 0x45, 0x45, 0x45, 0x39],
            '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
            '7': [0x01, 0x71, 0x09, 0x05, 0x03],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00]
        }

        # Convert the number to display data
        number_str = str(number)
        data = []
        for char in number_str:
            if char in font:
                data.extend(font[char] + [0x00])  # Add a blank column for spacing

        # Move cursor to the beginning of the first line
        self.write_command(0xB0)  # Page 0
        self.write_command(0x00)  # Lower column start address
        self.write_command(0x10)  # Higher column start address

        # Send the data to the OLED
        self.write_data(data[:128])  # Only display the data, limited to screen width

def is_prime(num):
    if num <= 1:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def generate_primes(oled):
    num = 2
    while True:
        if is_prime(num):
            oled.display_number(num)
           # time.sleep(0.01)  # 100ms delay between displaying numbers
        num += 1

if __name__ == "__main__":
    try:
        oled = OLED()
        generate_primes(oled)
    except Exception as e:
        print(e)
    finally:
        oled.close_device()
