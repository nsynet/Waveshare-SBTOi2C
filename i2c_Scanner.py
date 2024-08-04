import ctypes
import os

os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console screen at the beginning

# Load the Windows DLL for the CH347 device
dll_path = os.path.join(os.getcwd(), 'CH347DLLA64.dll')  # Ensure the correct path
ch347_dll = ctypes.windll.LoadLibrary(dll_path)

# Define argument types and return types for the DLL functions
ch347_dll.CH347OpenDevice.argtypes = [ctypes.c_uint]
ch347_dll.CH347OpenDevice.restype = ctypes.c_int

ch347_dll.CH347CloseDevice.argtypes = [ctypes.c_uint]
ch347_dll.CH347CloseDevice.restype = None

ch347_dll.CH347StreamI2C.argtypes = [
    ctypes.c_uint, ctypes.c_uint,
    ctypes.POINTER(ctypes.c_ubyte), ctypes.c_uint,
    ctypes.POINTER(ctypes.c_ubyte)
]
ch347_dll.CH347StreamI2C.restype = ctypes.c_int

class USBI2C:
    def __init__(self, usb_dev_index=0):
        self.dev_index = usb_dev_index
        self.open_device()

    def open_device(self):
        self.handle = ch347_dll.CH347OpenDevice(self.dev_index)
        if self.handle != -1:
            print(f"Opened device at index: {self.dev_index}")
        else:
            raise Exception("USB CH347 Open Failed!")

    def close_device(self):
        if self.handle != -1:
            ch347_dll.CH347CloseDevice(self.dev_index)
            print(f"Closed device at index: {self.dev_index}")

    def scan_i2c_bus(self):
        print("Scanning I2C bus...")
        grid = [['  ' for _ in range(16)] for _ in range(8)]
        found_devices = []

        for address in range(0x03, 0x78):  # Scan I2C address range
            write_buffer = (ctypes.c_ubyte * 1)(address << 1)  # Address as 7-bit write address
            read_buffer = (ctypes.c_ubyte * 1)()

            # Attempt to write a dummy command to see if the device acknowledges
            result = ch347_dll.CH347StreamI2C(self.dev_index, 1, write_buffer, 0, read_buffer)

            if result == 1:  # Non-zero indicates a device was acknowledged
                grid[address // 16][address % 16] = '* '
                found_devices.append(address)

        print("\nI2C Address Grid (marked with * where devices are found):")
        print("    " + "  ".join(f"{x:02X}" for x in range(16)))
        for i, row in enumerate(grid):
            print(f"{i * 16:02X}: " + " ".join(row))

        if found_devices:
            found_devices_str = ", ".join(f"0x{addr:02X}" for addr in found_devices)
            print(f"\nFound Device(s) at Address: {found_devices_str}")

def main():
    try:
        # Initialize the I2C device
        i2c_device = USBI2C(usb_dev_index=0)  # Adjust the index if necessary
        i2c_device.scan_i2c_bus()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        i2c_device.close_device()

if __name__ == "__main__":
    main()
