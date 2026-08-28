# System-1 Sensor 4/5 Addition — Status Report (In Progress)

**Date:** 2026-07-08
**System:** ifet fleet, device `system-1` / `device1`
**Scope:** Adding sensor4 and sensor5 to system-1, following the process in `README-sensor-debug-drill.md`, continuing from the 2026-07-07 debug (see `docs/hardware/system1-sensor-vfd-debug-2026-07-07.md`)

## 1. Summary

Sensors 1-3 and the VFD are fully working on system-1 (see the 2026-07-07 report). This session added sensor4 and sensor5 to reach the 5-sensor layout the site-b-device-1 config anticipates.

- **Sensor 4:** ✅ Added, wired, and confirmed working (customer validated with a real physical pressure change).
- **Sensor 5:** ⚠️ Wired and answering on the bus with zero communication failures, but its published value has been bit-identical across 5+ minutes of polling with no ADC-level jitter — the same "frozen/cached read" signature flagged in the 2026-07-07 report. **Not yet validated as a genuinely live reading.**
- **VFD / comm bus test:** not run this session — bus/VFD unavailable on system-1 at time of writing. Work paused, to resume with the customer.

## 2. What changed

`deployment/config/config1.json` on the system-1 host (`/home/labadm/ifet-firmware`, uncommitted, same pattern as the 2026-07-07 fixes):

- Backed up before editing: `config1.json.bak.1783523673`.
- Added two new sensor entries, matching the existing `pressure2`/scale 144/PSF convention used by sensors 1-3:

```json
{
  "name": "4",
  "address": "4",
  "debug": false,
  "value": "",
  "active": true,
  "type": "pressure2",
  "scale": 144,
  "unit": "PSF"
},
{
  "name": "5",
  "address": "5",
  "debug": false,
  "value": "",
  "active": true,
  "type": "pressure2",
  "scale": 144,
  "unit": "PSF"
}
```

- `docker restart ifet-firmware-serial_service-1` was sufficient to pick up each config change (config is bind-mounted at `/app/config.json`; no rebuild needed since no source change was involved this time).

## 3. Finding: the `active` config flag does not gate polling

While staging sensor4/5 as `active: false` (before they were physically wired) to avoid affecting the working setup, we found that `SensorHandler.add_sensor()` in `src/serial_service/sensors_handler/sensor_node.py` adds **every** entry in the `sensors` array to the polling list — it never checks `active`. This was confirmed both by reading the source and by observing the existing inactive `Flow` sensor (address 11) being polled and publishing `0` every cycle despite `active: false`.

**Implication:** `active: false` in this config is currently decorative only. Staging a new sensor as "inactive" does not prevent it from being polled — a not-yet-connected device configured this way will show up in the logs as a `NoResponseError` every cycle (harmless at `retries: 0`/`timeout: 0.1`, but worth knowing so it isn't mistaken for a real fault). If gating polling by config is ever needed, `add_sensor()` would need an explicit `if sensor_config.get("active", True):` check added.

## 4. Sensor 4 — confirmed working

Added at address 4, `pressure2`/reg 22, scale 144/PSF (same mapping as sensors 1-3). Communication succeeded immediately (no address-hunting needed, unlike the VFD on 2026-07-07). Live value showed natural small variation between polls even at idle (e.g. `-0.516351755708456` → `-0.516352292150259`), and the customer confirmed it visibly responds to a real applied pressure change. **No further action needed on sensor4.**

## 5. Sensor 5 — communication OK, data validity unconfirmed

Added at address 5, same `pressure2`/scale 144/PSF mapping. Observations:

- **0% communication failure rate** over multiple sampling windows — no `NoResponseError` logged at any point.
- **Value frozen:** published reading `0.09323640167713165` was bit-identical across every poll for 5+ minutes, with zero jitter — unlike sensor4 (jitter in the 6th decimal at idle) or sensors 1/2 (clear live variation).

Per the validation method established on 2026-07-07 ("a bit-identical value across 30s of polling... is the signature of a read that's silently failing and falling back to the last cached value, not a live sensor"), **a clean comms channel does not by itself prove sensor5 is reporting real data.** This must be confirmed with a live physical pressure/vacuum change before trusting it.

## 6. Open items / next steps (resume here)

1. **Physical validation of sensor5:** apply a real pressure/vacuum change on sensor5's line while tailing `docker logs -f ifet-firmware-serial_service-1 | grep 'sensor \[5\]'` and confirm the value actually tracks the change.
2. **If sensor5 stays frozen under a real pressure event:** treat it like the 2026-07-07 VFD address mystery — run a read-only broad Modbus address scan at register 22 (FC3) to rule out sensor5 actually living at a different address than assumed, avoiding collision with addresses already in use (1, 2, 3, 11 [Flow, unused], 12 [VFD]).
3. **VFD / bus test:** intentionally not run this session. Per the debug drill's safety note, commanding the VFD via MQTT (`set_frequency`/`start`) physically starts the motor/turbo hardware — needs the equipment owner's (customer's) go-ahead on timing/frequency before it's triggered, not something to run unilaterally.
4. **Commit outstanding changes:** as with the 2026-07-07 fixes, this session's `config1.json` edits are uncommitted on the system-1 host only. Combine with the still-open 2026-07-07 commit decision (see that report's §6) once the site-b config migration question is settled.
5. **Sensor address map on system-1 (current, uncommitted, live):** sensor1=1, sensor2=2, sensor3=3, sensor4=4, sensor5=5, Flow=11 (inactive/unused), VFD=12.
