# Waveshare To i2c, UART, SPI, JTAG

CH347DLLA64.dll Usage Guide
The CH347DLLA64.dll library enables communication with the CH347 USB-to-serial interface chip, providing functionality for I2C, SPI, and GPIO operations. This guide outlines its primary functions and usage.

Features
I2C Communication: Supports I2C read/write operations, making it ideal for interfacing with various I2C devices.
SPI Communication: Capable of SPI transactions for high-speed data transfer.
GPIO Control: Offers GPIO pin control for general-purpose use.
Multi-Platform Support: Compatible with multiple Windows versions and devices using the CH347 chip.


# Functions Overview. - Python
Device Management 

  CH347OpenDevice: Opens a connection to the CH347 device. Returns a handle used for further operations.
device_handle = ch347_dll.CH347OpenDevice(device_index)

  CH347CloseDevice: Closes the connection to the CH347 device.
ch347_dll.CH347CloseDevice(device_handle)

# I2C Operations
  CH347I2C_Set: Configures the I2C interface, such as setting the I2C clock speed.
result = ch347_dll.CH347StreamI2C(device_handle, write_length, write_buffer, read_length, read_buffer)

# Example Usage
import ctypes

# Load DLL
ch347_dll = ctypes.windll.LoadLibrary("CH347DLLA64.dll")

# Open Device
device_index = 0
device_handle = ch347_dll.CH347OpenDevice(device_index)
if device_handle == -1:
    raise Exception("Failed to open CH347 device")

# Initialize I2C
i2c_speed = 0x20  # Example speed value
if not ch347_dll.CH347I2C_Set(device_handle, i2c_speed):
    raise Exception("Failed to set I2C speed")

# Perform I2C Read/Write
write_data = (ctypes.c_ubyte * 3)(0xA0, 0x00, 0x01)  # Example write data
read_data = (ctypes.c_ubyte * 2)()
success = ch347_dll.CH347StreamI2C(device_handle, len(write_data), write_data, len(read_data), read_data)
if not success:
    raise Exception("Failed to perform I2C transaction")

# Close Device
ch347_dll.CH347CloseDevice(device_handle)
