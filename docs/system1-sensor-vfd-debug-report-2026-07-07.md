# System-1 Sensor / VFD Communication Debug Report

**Date:** 2026-07-07
**System:** ifet fleet, device `system-1` / `device1`
**Scope:** Full sensor + VFD communication debug, following the process documented in `README-sensor-debug-drill.md` (originally written for system-2)

## 1. Summary

`system-1` was found completely non-functional at the start of this session: the `serial_service` container wasn't even running, and once started, all three pressure sensors and the VFD failed 100% of the time. Through systematic isolation, all four devices were brought to full working order:

- **Sensor 1, 2, 3:** fixed by correcting the register map (`pressure` → `pressure2`) and validated live with real physical pressure changes on each.
- **VFD:** fixed by correcting the Modbus slave address (`5` → `12`).
- **Root hardware identity:** discovered mid-session that `system-1` is physically the **site-b-device-1** unit referenced elsewhere in the repo, not a generic lab rig — this explains both the VFD address and why the generic config was wrong for it.
- **Unit conversion:** added optional PSI→PSF conversion for system-1's sensors per customer request, via a small, config-driven code change.

All communications-level issues are now resolved. All fixes are config changes on system-1's deployment, except the PSI/PSF unit conversion, which required one small source code change.

## 2. System configuration

- Host: Raspberry Pi (`system-1`), running Python services (`sensor_node.py`/`serial_com.py`, using `minimalmodbus`/`pyserial`), managed via `docker compose -f docker-compose-1.yaml`.
- Serial port: `/dev/ttyUSB0` (FTDI FT232R, serial `BG00Y9T9`) — was misconfigured as `/dev/ttyACM0`.
- Mode: Modbus RTU, 9600 baud, 8N1.
- Three pressure sensors + one VFD share a single serial connection and software lock.

| Device | Modbus address | Register / function | Status at session start | Status at session end |
|---|---|---|---|---|
| Sensor 1 | 1 | reg 22, float, no scale (`pressure2`) | 100% fail ("illegal function" — wrong register) | ✅ Working, live-validated |
| Sensor 2 | 2 | reg 22, float, no scale (`pressure2`) | Not connected yet | ✅ Working, live-validated (once connected) |
| Sensor 3 | 3 | reg 22, float, no scale (`pressure2`) | Not connected yet | ✅ Working, live-validated (once connected) |
| VFD | **12** (was configured as 5) | reg 8451 FC3 (feedback), writes at 8192/8193 | 100% fail ("no answer") | ✅ Working |

## 3. Root causes found, in order of discovery

### 3.1 `serial_service` container never started

`config1.json` and `docker-compose-1.yaml` both hardcoded `/dev/ttyACM0` as the serial device, but the actual attached adapter enumerates as `/dev/ttyUSB0` (confirmed via `/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_BG00Y9T9-if00-port0 -> ttyUSB0`). `docker compose up` failed outright with `error gathering device information while adding custom device "/dev/ttyACM0": no such file or directory` — the container had never successfully been created.

**Fix:** updated the device path to `/dev/ttyUSB0` in both `config1.json` and `docker-compose-1.yaml`.

### 3.2 Sensors 1/2/3: wrong register map

All three sensors were configured `"type": "pressure"`, which reads holding register `1028` (×144 scale) via `sensor.py`. This is the mapping that works for system-2's sensor 1, but on system-1:

- Sensor 1 returned a real Modbus exception every time: `Slave reported illegal function` — proof the device was alive and answering, just rejecting that register/function.
- Sensors 2/3 (once connected) returned `No communication with the instrument (no answer)` under the same wrong mapping.

Switching all three to `"type": "pressure2"` (register `22`, no scale, handled by `new_sensor.py`) fixed all three immediately — 0% failure rate, confirmed with live data.

**Validation method:** isolating a sensor in the config and seeing it "read successfully" is not sufficient proof it's alive — a sensor stuck on its last/initial cached value can look identical to a genuinely idle sensor. Each sensor was confirmed by watching its live MQTT/log output while a real physical pressure change was applied and observing the value actually move:

- Sensor 1: baseline `0.00223` (frozen) → real pressure applied → oscillated between `-0.0231` / `-0.0227`, later swept `0.207 → 0.093` during a VFD-driven pressure event.
- Sensor 2: baseline `-0.00305` (frozen) → real pressure applied → swept `0.207 → 0.204 → 0.202 → 0.200 → 0.184 → 0.134 → 0.109 → 0.094`.
- Sensor 3: baseline `4.2e-05` (frozen) → real pressure applied → swept `0.185 → 0.231 → 0.734 → 0.668 → 0.138 → 0.232 → 0.380 → 0.335 → 0.693`.

### 3.3 VFD: wrong Modbus address

The VFD was configured at address `5` and was **completely unreachable** under every condition tested:

- Timeout sweep: 50ms, 200ms, 500ms, 1s — no change, always `NoResponseError`.
- Baud rate sweep: 9600 / 19200 / 4800 / 38400 / 2400 — no response at any rate.
- Parity/stop-bit sweep: N/E/O × 1/2 stop bits, all combinations — no clean response.
- Broad address scan 0–10 at the VFD's feedback register (8451, FC3) — only address 1 (sensor 1) answered; nothing else responded, ruling out an address collision with sensors 2/3.
- `close_port_after_each_call` toggled — no effect.

This ruled out every software/config explanation, pointing to either a physical fault or a wrong address.

**Root cause:** address `5` is simply wrong for this hardware. The real cause was discovered via an **untracked runbook** in the repo (`deployment/split-serial-temp/README.md`, dated 2026-07-02, never committed to git) documenting that this exact FTDI adapter (serial `BG00Y9T9`) is the dedicated VFD bus for "site-b device 1", with the VFD at **Modbus address 12**. Testing address 12 confirmed it immediately (`read_register(8451, 2, functioncode=3)` → `OK value=0`).

**This also revealed that `system-1` is physically the site-b-device-1 hardware** referenced elsewhere in the repo (`docker-compose-site-b-device-1.yaml`, `deployment/config/config1-site-b.json`) — not a generic lab rig. That config already has the correct sensor types (`pressure2` for sensors 1–5) and VFD address (12) baked in; the live `config1.json` running on `system-1` was the generic 3-sensor/VFD@5 config, which was simply the wrong config for this actual unit.

**Fix:** changed `vfd.address` from `"5"` to `"12"` in `config1.json`. Confirmed working immediately — VFD feedback reads cleanly every poll, frequency ramped correctly (3 → 6 → 8.5 Hz) during a live customer test.

### 3.4 Downstream "all sensors reading 0.00" during a live test (not a bug)

Partway through validation, the admin dashboard showed sensor readings as `0.00` while a live test ran and the VFD frequency ramped. Investigation (checking the raw MQTT feed, comparing to `round(value, 3)` in the publish code, and cross-referencing the dashboard screenshot) showed this was **not a regression** — it was two combined, expected factors:

1. Sensors 1/2's true idle-baseline values (`~0.002`, `~-0.003`) are small enough to display as `0.00` at 2 decimal places on the dashboard.
2. The physical pressure hose for that test hadn't been connected yet on the customer's end. Sensor 3 (the one actually plumbed to the active line) showed a real, moving value (`-0.03`) the whole time, confirming the pipeline was working correctly — sensors 1/2 were correctly flat because nothing was pressurizing their lines.

Once the hose was connected, no further action was needed — this was purely a physical-setup timing issue on the customer's side, not a software fault.

## 4. Unit conversion: PSI → PSF (system-1 only)

Customer requested sensor readings be reported in PSF instead of PSI. The `pressure2` sensor class (`new_sensor.py`) had no scale factor and hardcoded the `PSI` label. Added optional `scale`/`unit` config fields (default `1` / `"PSI"`, preserving existing behavior for anything not opted in):

```python
self.scale = float(config.get("scale", 1))
self.unit = config.get("unit", "PSI")
...
self.last_t = self.com_port.read_float(self.address, 22, 3) * self.scale
self.logger.info(f'sensor [{self.address}] value {self.last_t} {self.unit}')
```

System-1's sensors 1–3 were set to `"scale": 144, "unit": "PSF"` in `config1.json`. Rebuilt and redeployed `serial_service`; confirmed correct conversion:

```
sensor 1: 0.3208 PSF   (0.00223 PSI × 144)
sensor 2: -0.5043 PSF  (-0.0035 PSI × 144)
sensor 3: -0.0566 PSF  (-0.00039 PSI × 144)
```

**Scope decision:** applied to system-1 only, per customer request. `system-2` was not touched — its containers, config, and running code are unaffected, and the new field's default (`1`/`"PSI"`) means it would behave identically even if it later picks up the same image.

## 5. Final state

| Component | Status |
|---|---|
| `serial_service` container | ✅ Running (was never starting before) |
| Sensor 1 | ✅ Working — `pressure2`/reg 22, PSF output |
| Sensor 2 | ✅ Working — `pressure2`/reg 22, PSF output |
| Sensor 3 | ✅ Working — `pressure2`/reg 22, PSF output |
| VFD | ✅ Working — address 12 |

### What changed, and where it lives

- **Config-only changes** (uncommitted on the `system-1` host, `/home/labadm/ifet-firmware`): `deployment/config/config1.json` (device path, sensor types, `scale`/`unit`, `retries: 0`, `timeout: 0.1`, `vfd.address: 12`) and `docker-compose-1.yaml` (device path).
- **Source code change** (also uncommitted, both on the system-1 host and in this local repo checkout): `src/serial_service/sensors_handler/new_sensor.py` — added optional `scale`/`unit` support. Deployed to system-1 via `docker compose build serial_service`.

## 6. Open items / recommendations

1. **Formal config migration:** consider moving `system-1` fully onto `docker-compose-site-b-device-1.yaml` + `config1-site-b.json` (which already define the correct 5-sensor, VFD@12 layout) instead of continuing to patch the generic `config1.json`. Not done yet — flagged for a future decision.
2. **Commit the changes:** the `new_sensor.py` scale/unit change and the `config1.json`/`docker-compose-1.yaml` fixes are currently uncommitted, both on the system-1 host and in this local repo. Nothing has been pushed. Recommend committing once the site-b migration question above is settled, to avoid committing twice.
3. **Sensors 4/5:** the site-b project schema (and admin dashboard) anticipate 5 sensors; system-1's current physical setup only has 3 wired. If sensors 4/5 are added later, they'll need the same `pressure2`/register-22 + `scale`/`unit` treatment validated here.
