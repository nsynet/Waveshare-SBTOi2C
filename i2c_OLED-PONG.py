import time
from ctypes import *
import random

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

# Game parameters
screen_width = 128
screen_height = 64
paddle_width = 2
paddle_height = 12
ball_size = 2
paddle_speed = 8  # Increased paddle movement speed
ball_speed = 5  # Increased ball speed

class OLED:
    def __init__(self, usb_dev=0, i2c_addr=0x3C):  # Default I2C address for OLED
        self.usb_id = usb_dev
        self.dev_addr = i2c_addr
        self.width = screen_width
        self.height = screen_height
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

    def draw_rect(self, x, y, width, height, color=1):
        for i in range(width):
            for j in range(height):
                self.draw_pixel(x + i, y + j, color)

    def update_display(self):
        # Write the buffer to the display
        for page in range(self.pages):
            self.write_command(0xB0 + page)  # Set page address
            self.write_command(0x00)         # Set lower column address
            self.write_command(0x10)         # Set higher column address
            start = page * self.width
            self.write_data(self.buffer[start:start + self.width])

class PongGame:
    def __init__(self, oled):
        self.oled = oled
        self.paddle1_y = (screen_height - paddle_height) // 2
        self.paddle2_y = (screen_height - paddle_height) // 2
        self.ball_x = screen_width // 2
        self.ball_y = screen_height // 2
        self.ball_dx = random.choice([-1, 1]) * ball_speed
        self.ball_dy = random.choice([-1, 1]) * ball_speed

    def update(self):
        # Update ball position
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Ball collision with top and bottom
        if self.ball_y <= 0 or self.ball_y >= screen_height - ball_size:
            self.ball_dy *= -1

        # Ball collision with paddles
        if self.ball_x <= paddle_width:  # Left paddle
            if self.paddle1_y <= self.ball_y <= self.paddle1_y + paddle_height:
                self.ball_dx *= -1
                self.ball_dy = random.choice([-1, 1]) * ball_speed
            else:
                self.reset_ball()

        if self.ball_x >= screen_width - paddle_width - ball_size:  # Right paddle
            if self.paddle2_y <= self.ball_y <= self.paddle2_y + paddle_height:
                self.ball_dx *= -1
                self.ball_dy = random.choice([-1, 1]) * ball_speed
            else:
                self.reset_ball()

        # Conditional AI movement for paddles
        if self.ball_dx < 0:  # Move left paddle if ball moving towards it
            self.paddle1_y = self.paddle_ai(self.paddle1_y, self.ball_y)
        else:  # Move right paddle if ball moving towards it
            self.paddle2_y = self.paddle_ai(self.paddle2_y, self.ball_y)

    def paddle_ai(self, paddle_y, ball_y):
        # AI paddles will follow the ball
        if paddle_y + paddle_height // 2 < ball_y:
            paddle_y += paddle_speed
        elif paddle_y + paddle_height // 2 > ball_y:
            paddle_y -= paddle_speed

        # Ensure paddles stay within screen bounds
        paddle_y = max(0, min(paddle_y, screen_height - paddle_height))

        return paddle_y

    def reset_ball(self):
        self.ball_x = screen_width // 2
        self.ball_y = screen_height // 2
        self.ball_dx = random.choice([-1, 1]) * ball_speed
        self.ball_dy = random.choice([-1, 1]) * ball_speed

    def draw(self):
        # Clear the display buffer
        self.oled.clear_display()

        # Draw paddles and ball
        self.oled.draw_rect(0, self.paddle1_y, paddle_width, paddle_height, 1)  # Left paddle
        self.oled.draw_rect(screen_width - paddle_width, self.paddle2_y, paddle_width, paddle_height, 1)  # Right paddle
        self.oled.draw_rect(self.ball_x, self.ball_y, ball_size, ball_size, 1)  # Ball

        # Update the OLED display
        self.oled.update_display()

def main(oled):
    game = PongGame(oled)
    while True:
        game.update()
        game.draw()
        time.sleep(0.005)  # Faster game loop

if __name__ == "__main__":
    try:
        oled = OLED()
        main(oled)
    except Exception as e:
        print(e)
    finally:
        oled.close_device
