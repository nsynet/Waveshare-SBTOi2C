import time
from ctypes import *
from datetime import datetime

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

# Adjustable parameters
text_size = 2  # Scaling factor for text size

class OLED:
    def __init__(self, usb_dev=0, i2c_addr=0x3C):  # Default I2C address for OLED
        self.usb_id = usb_dev
        self.dev_addr = i2c_addr
        self.width = 128
        self.height = 64
        self.pages = self.height // 8

        # Create a buffer for the display
        self.buffer = [0x00] * (self.width * self.pages)

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
        # Clear the buffer
        self.buffer = [0x00] * (self.width * self.pages)

        # Write the buffer to the display
        for page in range(self.pages):
            self.write_command(0xB0 + page)  # Set page address
            self.write_command(0x00)         # Set lower column address
            self.write_command(0x10)         # Set higher column address
            start = page * self.width
            self.write_data(self.buffer[start:start + self.width])

    def draw_pixel(self, x, y, color=1):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return  # Out of bounds

        page = y // 8
        bit = y % 8
        index = x + page * self.width

        if color:
            self.buffer[index] |= (1 << bit)
        else:
            self.buffer[index] &= ~(1 << bit)

    def draw_text(self, x, y, text, size=1, color=1):
        # A very basic font array for demonstration purposes
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
            ':': [0x00, 0x36, 0x36, 0x00, 0x00],
            '-': [0x08, 0x08, 0x08, 0x08, 0x08],
            '/': [0x20, 0x10, 0x08, 0x04, 0x02],
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            'A': [0x7C, 0x12, 0x11, 0x12, 0x7C],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x04, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x46, 0x49, 0x49, 0x49, 0x31],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x3C, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
            'Z': [0x61, 0x51, 0x49, 0x45, 0x43]
        }

        for char in text:
            if char in font:
                char_data = font[char]
                for i, line in enumerate(char_data):
                    for j in range(8):
                        pixel = (line >> j) & 0x01
                        if pixel:
                            for dx in range(size):
                                for dy in range(size):
                                    self.draw_pixel(x + i * size + dx, y + j * size + dy, color)
                x += 6 * size

    def update_display(self):
        # Write the buffer to the display
        for page in range(self.pages):
            self.write_command(0xB0 + page)  # Set page address
            self.write_command(0x00)         # Set lower column address
            self.write_command(0x10)         # Set higher column address
            start = page * self.width
            self.write_data(self.buffer[start:start + self.width])

def display_time_and_date(oled, width=128, height=64):
    # Calculate the initial positions for centering text
    time_x = (width - 8 * 6 * text_size) // 2  # 8 characters for "HH:MM:SS"
    date_x = (width - 10 * 6 * text_size) // 2  # 10 characters for "MM/DD/YYYY"
    y_time = (height // 4)  # Top quarter for the time
    y_date = y_time + text_size * 8 + 2  # Just below the time

    prev_time = ""
    prev_date = ""

    while True:
        # Get current time and date
        now = datetime.now()
        time_text = now.strftime("%H:%M:%S")
        date_text = now.strftime("%m/%d/%Y")

        # Update buffer only for changed characters
        if time_text != prev_time:
            # Clear only the part where the time is displayed
            for i in range(len(prev_time)):
                if i >= len(time_text) or time_text[i] != prev_time[i]:
                    char_x = time_x + i * 6 * text_size
                    for j in range(text_size * 8):
                        for k in range(6 * text_size):
                            oled.draw_pixel(char_x + k, y_time + j, 0)

            oled.draw_text(time_x, y_time, time_text, size=text_size)

        if date_text != prev_date:
            # Clear only the part where the date is displayed
            for i in range(len(prev_date)):
                if i >= len(date_text) or date_text[i] != prev_date[i]:
                    char_x = date_x + i * 6 * text_size
                    for j in range(text_size * 8):
                        for k in range(6 * text_size):
                            oled.draw_pixel(char_x + k, y_date + j, 0)

            oled.draw_text(date_x, y_date, date_text, size=text_size)

        # Update display
        oled.update_display()

        # Update previous text
        prev_time = time_text
        prev_date = date_text

        time.sleep(0.1)  # Adjust this delay for real-time updates

if __name__ == "__main__":
    try:
        oled = OLED()
        display_time_and_date(oled)
    except Exception as e:
        print(e)
    finally:
        oled.close_device()
