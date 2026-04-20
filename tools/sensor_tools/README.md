# sensor_tools

Modbus RTU utilities for configuring and scanning sensors on a serial bus.

## Requirements

```
pip install minimalmodbus
```

---

## chaddr.py — Change address (old device)

Targets old device firmware using register `0x0300` and function code `0x10`.

```bash
python chaddr.py <serial_port> <old_address> <new_address>
```

**Example:**

```bash
python chaddr.py /dev/ttyUSB0 1 5
```

---

## chaddr_new_sensor.py — Change address (SenTec sensor)

Targets SenTec sensors. Writes new address to register `0` (FC 6), then saves permanently by writing `0` to register `65535`.

```bash
python chaddr_new_sensor.py <serial_port> <old_address> <new_address>
```

- `new_address` must be in range **1–255**

**Example:**

```bash
python chaddr_new_sensor.py /dev/ttyUSB0 1 3
```

---

## configure_address.py — GUI address configurator

Tkinter GUI supporting both SenTec and old device types. Select device type, enter port and addresses, click **Change Address**.

```bash
python configure_address.py
```

**Fields:**
| Field | Description |
|---|---|
| Device Type | `SenTec` (register 0 + save) or `Old Device` (register 0x0300) |
| Serial Port | e.g. `/dev/ttyUSB0` or `COM3` |
| Current Address | Existing Modbus slave address |
| New Address | Target address (1–255) |

---

## scanner.py — Scan for active Modbus devices

Polls addresses 1–247, reports which ones respond to a register read (FC 3, register 1).

```bash
python scanner.py <serial_port>
```

**Example:**

```bash
python scanner.py /dev/ttyUSB0
```

Output lists every responding address:

```
Scanning Modbus addresses from 1 to 247...
Address 3 is available.
Address 11 is available.
Available addresses: [3, 11]
```

> Scan is slow by default (1s timeout × 247 addresses). Reduce timeout in source if needed.
