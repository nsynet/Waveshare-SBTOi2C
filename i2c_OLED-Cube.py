import time
import math
from ctypes import *

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

# Adjustable parameters
cube_size = 30  # Size of the cube
center_x = 64  # Center of the display (width // 2)
center_y = 32  # Center of the display (height // 2)

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

    def draw_line(self, x0, y0, x1, y1, color=1):
        # Implement Bresenham's line algorithm
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.draw_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def update_display(self):
        # Write the buffer to the display
        for page in range(self.pages):
            self.write_command(0xB0 + page)  # Set page address
            self.write_command(0x00)         # Set lower column address
            self.write_command(0x10)         # Set higher column address
            start = page * self.width
            self.write_data(self.buffer[start:start + self.width])

def rotate_point(point, angle_x, angle_y, angle_z):
    # Rotation matrices around x, y, and z axes
    sin_x, cos_x = math.sin(angle_x), math.cos(angle_x)
    sin_y, cos_y = math.sin(angle_y), math.cos(angle_y)
    sin_z, cos_z = math.sin(angle_z), math.cos(angle_z)

    # Rotate around x-axis
    x1 = point[0]
    y1 = point[1] * cos_x - point[2] * sin_x
    z1 = point[1] * sin_x + point[2] * cos_x

    # Rotate around y-axis
    x2 = x1 * cos_y + z1 * sin_y
    y2 = y1
    z2 = -x1 * sin_y + z1 * cos_y

    # Rotate around z-axis
    x3 = x2 * cos_z - y2 * sin_z
    y3 = x2 * sin_z + y2 * cos_z
    z3 = z2

    return (x3, y3, z3)

def project_point(point, center_x, center_y, scale):
    # Project a 3D point onto a 2D plane
    x = int(point[0] * scale + center_x)
    y = int(point[1] * scale + center_y)
    return (x, y)

def draw_cube(oled, cube_vertices, edges, angle_x, angle_y, angle_z):
    # Create a temporary buffer to track changes
    new_buffer = [0x00] * len(oled.buffer)

    # Rotate and project each vertex of the cube
    projected_vertices = []
    for vertex in cube_vertices:
        rotated_vertex = rotate_point(vertex, angle_x, angle_y, angle_z)
        projected_vertex = project_point(rotated_vertex, center_x, center_y, 1)
        projected_vertices.append(projected_vertex)

    # Draw each edge of the cube
    for edge in edges:
        start_vertex = projected_vertices[edge[0]]
        end_vertex = projected_vertices[edge[1]]
        # Draw the line directly into the new buffer
        draw_line_in_buffer(new_buffer, start_vertex[0], start_vertex[1], end_vertex[0], end_vertex[1])

    # Copy the new buffer to the OLED's buffer if there are changes
    if new_buffer != oled.buffer:
        oled.buffer = new_buffer
        oled.update_display()

def draw_line_in_buffer(buffer, x0, y0, x1, y1, color=1):
    # Implement Bresenham's line algorithm directly in the buffer
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if 0 <= x0 < 128 and 0 <= y0 < 64:  # Ensure drawing within bounds
            page = y0 // 8
            bit = y0 % 8
            index = x0 + page * 128
            if color:
                buffer[index] |= (1 << bit)
            else:
                buffer[index] &= ~(1 << bit)
        if x0 == x1 and y0 == y1:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def main(oled):
    # Define the vertices of a cube centered around the origin
    half_size = cube_size / 2
    cube_vertices = [
        (-half_size, -half_size, -half_size), (half_size, -half_size, -half_size),
        (half_size, half_size, -half_size), (-half_size, half_size, -half_size),
        (-half_size, -half_size, half_size), (half_size, -half_size, half_size),
        (half_size, half_size, half_size), (-half_size, half_size, half_size)
    ]

    # Define the edges of the cube (pairs of vertex indices)
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Back face
        (4, 5), (5, 6), (6, 7), (7, 4),  # Front face
        (0, 4), (1, 5), (2, 6), (3, 7)   # Connecting edges
    ]

    angle_x, angle_y, angle_z = 0, 0, 0  # Initial angles

    while True:
        # Draw the rotating cube
        draw_cube(oled, cube_vertices, edges, angle_x, angle_y, angle_z)

        # Increment rotation angles faster for smoother animation
        angle_x += 0.1
        angle_y += 0.07
        angle_z += 0.05

        # Reduce sleep time for a smoother animation
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        oled = OLED()
        main(oled)
    except Exception as e:
        print(e)
    finally:
        oled.close_device()
