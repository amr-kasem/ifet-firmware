# testing_tools

Tools for testing and simulating IFET device behavior over MQTT and Modbus.

## Requirements

```
pip install paho-mqtt minimalmodbus
```

MQTT broker (e.g. Mosquitto) must be running locally on port `1883` for MQTT tools.

---

## fake_sensor.py — Publish fake sensor data

Publishes random humidity values to MQTT topic `device1/sensors/4` every 5 seconds. Simulates a sensor for integration testing.

```bash
python fake_sensor.py
```

- Broker: `localhost:1883`
- Topic: `device1/sensors/4`
- Payload: humidity float (40–60 range, 2 decimal places)

Stop with `Ctrl+C`.

> Edit `broker_address`, `broker_port`, and `topic` at the top of the file to target a different broker or topic.

---

## flow_meter.py — Read flow meter register

Reads a 32-bit unsigned integer from a Modbus flow meter at `/dev/ttyACM0`, slave address `11`, register `0x042D`. Decodes two 16-bit registers as big-endian and divides by 10000.

```bash
python flow_meter.py
```

> Edit `instrument` port/address and `register_address` in the source to match your device.

---

## test.py — Interactive MQTT device client

Curses-based interactive terminal UI. Connects to an MQTT broker and lets you monitor sensor data, VFD feedback, valve status, and system state — and send control commands in real time.

```bash
python test.py [--host HOST] [--port PORT] [--device DEVICE_ID]
```

**Arguments:**

| Argument | Default | Description |
|---|---|---|
| `--host` | `localhost` | MQTT broker host |
| `--port` | `1883` | MQTT broker port |
| `--device` | `device1` | Device ID prefix for topics |

**Example:**

```bash
python test.py --host 192.168.1.10 --device device2
```

**Interactive commands:**

| Command | Action |
|---|---|
| `help` | List available commands |
| `vfd` | Send VFD command (`start` / `stop` / `set_frequency` / `emergency_stop`) |
| `valve` | Set valve state by name (`0` = off, `1` = on) |
| `sensor` | Print current sensor readings |
| `status` | Print full status (state, VFD, valves, sensors) |
| `state` | Send state command (`start` / `stop` / `pause` / `resume`) |
| `quit` | Exit |

**MQTT topics used:**

| Direction | Topic pattern |
|---|---|
| Subscribe | `<device_id>/sensors/#` |
| Subscribe | `<device_id>/vfd/feedback` |
| Subscribe | `<device_id>/valves/status` |
| Subscribe | `<device_id>/state` |
| Publish | `<device_id>/vfd/command` |
| Publish | `<device_id>/valves/<name>` |
| Publish | `<device_id>/state/command` |
