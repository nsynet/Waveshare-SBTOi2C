import time
import random
from ctypes import *

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

# Adjustable parameters
grid_width = 128  # Width of the grid in cells
grid_height = 64  # Height of the grid in cells
cell_size = 1  # Size of each cell on the OLED (4x4 pixels)

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

    def draw_cell(self, x, y, size=1, color=1):
        for i in range(size):
            for j in range(size):
                self.draw_pixel(x + i, y + j, color)

    def update_display(self):
        # Write the buffer to the display
        for page in range(self.pages):
            self.write_command(0xB0 + page)  # Set page address
            self.write_command(0x00)         # Set lower column address
            self.write_command(0x10)         # Set higher column address
            start = page * self.width
            self.write_data(self.buffer[start:start + self.width])

def initialize_grid(width, height):
    # Create a random initial state for the grid
    return [[random.choice([0, 1]) for _ in range(width)] for _ in range(height)]

def count_neighbors(grid, x, y):
    # Count the live neighbors of a cell at position (x, y)
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    count = 0
    for dx, dy in directions:
        nx, ny = (x + dx) % len(grid[0]), (y + dy) % len(grid)
        count += grid[ny][nx]
    return count

def update_grid(grid):
    # Create a new grid to store the updated state
    new_grid = [[0 for _ in range(len(grid[0]))] for _ in range(len(grid))]
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            neighbors = count_neighbors(grid, x, y)
            if grid[y][x] == 1:
                # Any live cell with two or three live neighbors survives
                if neighbors == 2 or neighbors == 3:
                    new_grid[y][x] = 1
                else:
                    new_grid[y][x] = 0
            else:
                # Any dead cell with exactly three live neighbors becomes a live cell
                if neighbors == 3:
                    new_grid[y][x] = 1
    return new_grid

def display_grid(oled, current_grid, previous_grid, size):
    # Update only the cells that have changed
    for y in range(len(current_grid)):
        for x in range(len(current_grid[y])):
            if current_grid[y][x] != previous_grid[y][x]:
                color = current_grid[y][x]
                oled.draw_cell(x * size, y * size, size, color)

    # Update the OLED display
    oled.update_display()

def game_of_life(oled, grid_width=32, grid_height=16, cell_size=4):
    # Initialize a grid with a random pattern
    grid = initialize_grid(grid_width, grid_height)
    previous_grid = [[0 for _ in range(grid_width)] for _ in range(grid_height)]

    while True:
        # Display the current grid with only changes
        display_grid(oled, grid, previous_grid, cell_size)

        # Update the grid to the next generation
        previous_grid = grid
        grid = update_grid(grid)

        # Control the speed of the simulation
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        oled = OLED()
        game_of_life(oled, grid_width=grid_width, grid_height=grid_height, cell_size=cell_size)
    except Exception as e:
        print(e)
    finally:
        oled.close_device()
