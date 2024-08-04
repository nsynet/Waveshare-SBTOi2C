# Waveshare To i2c, UART, SPI, JTAG

CH347DLLA64.dll Usage Guide
The CH347DLLA64.dll library enables communication with the CH347 USB-to-serial interface chip, providing functionality for I2C, SPI, and GPIO operations. This guide outlines its primary functions and usage.

Features
I2C Communication: Supports I2C read/write operations, making it ideal for interfacing with various I2C devices.
SPI Communication: Capable of SPI transactions for high-speed data transfer.
GPIO Control: Offers GPIO pin control for general-purpose use.
Multi-Platform Support: Compatible with multiple Windows versions and devices using the CH347 chip.


Functions Overview

Device Management 
python
  CH347OpenDevice: Opens a connection to the CH347 device. Returns a handle used for further operations.
device_handle = ch347_dll.CH347OpenDevice(device_index)

  CH347CloseDevice: Closes the connection to the CH347 device.
ch347_dll.CH347CloseDevice(device_handle)

# I2C Operations
CH347I2C_Set: Configures the I2C interface, such as setting the I2C clock speed.
