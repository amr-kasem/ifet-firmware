import minimalmodbus
import serial
import sys
import time

def scan_modbus_addresses(
    port,
    baudrate=9600,
    timeout=0.5,
    start_address=1,
    end_address=247
):
    print(f"Opening {port} @ {baudrate} baud")

    instrument = minimalmodbus.Instrument(port, 1, mode=minimalmodbus.MODE_RTU)

    # Serial config
    instrument.serial.baudrate = baudrate
    instrument.serial.bytesize = 8
    instrument.serial.parity   = serial.PARITY_NONE
    instrument.serial.stopbits = 1
    instrument.serial.timeout  = timeout

    instrument.clear_buffers_before_each_transaction = True
    instrument.close_port_after_each_call = False
    instrument.debug = False

    found = []

    print(f"Scanning Modbus addresses {start_address} → {end_address}\n")

    for address in range(start_address, end_address + 1):
        instrument.address = address

        try:
            # Try multiple common probes
            instrument.read_register(0, 0, functioncode=3)
            print(f"✔ Found device at address {address}")
            found.append(address)

        except minimalmodbus.NoResponseError:
            pass
        except minimalmodbus.InvalidResponseError:
            print(f"⚠ Invalid response from address {address} (device exists)")
            found.append(address)
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            break
        except Exception:
            pass

        time.sleep(0.05)  # VERY important for RS485 stability

    print("\nScan finished.")
    print("Detected addresses:", found)

    return found


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scan_modbus.py /dev/ttyUSB0 [baudrate]")
        sys.exit(1)

    port = sys.argv[1]
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 9600

    scan_modbus_addresses(port, baudrate=baud)
