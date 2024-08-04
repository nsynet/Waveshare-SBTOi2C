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

# Error Handling
Always check return values for success and handle exceptions to ensure robust applications.

# Conclusion
The CH347DLLA64.dll provides a powerful interface for communicating with devices via I2C, SPI, and GPIO. For detailed documentation, refer to the manufacturer's guide.

# Project Overview
This project demonstrates the use of the CH347DLLA64.dll library to interface with various hardware components using a CH347 USB-to-serial interface chip. The main components used in this project are:

DS3231 Real-Time Clock (RTC) Module: Reads the current time and date, and sets the RTC if the stored time is incorrect.

OLED Display: Displays the current time and date in a formatted manner, updating only when necessary to minimize flickering.

Adafruit 7-segment LED Display: Displays the current time using a 7-segment format, with toggling colon for second indication.

# Program Descriptions
I2C Scanner
A utility script to scan for connected I2C devices, helping verify connections and addresses for connected components.

# RTC Time Display
Reads the time from a DS3231 RTC module. If the time is incorrect by a year, day, month, hour, minute, or 15 seconds, the program sets the correct time and date.

# Features:
Displays the current time, date, and day of the week on an OLED.
Updates only when the display content changes, reducing flicker.
LED Clock Display
Outputs the time to a 7-segment LED display using the HT16K33 controller.

# Features:
Formats time into hour and minute segments.
Toggles the colon for indicating seconds without display flickering.
