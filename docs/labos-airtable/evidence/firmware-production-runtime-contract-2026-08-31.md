# LabOS Production Firmware Runtime Contract

**Date:** 2026-08-31 · **Author:** gad · **Type:** evidence (read-only production audit)
**Nodes:** `system-1`, `system-2`, `management` · **Command log:** `firmware-production-probe-2026-08-31.txt`
**Companion (management/DB side):** `labos-real-data-types-2026-08-31.md`

> **Read this as an audit of reality, not a confirmation of design.** Where production
> contradicts `CLAUDE.md`, `docs/`, or the write contract, production wins and the
> contradiction is called out rather than reconciled away. Four of our own standing
> claims are corrected in §13.

---

## 1. Executive Summary

**The single most important finding: Firmware performs no test-programme derivation at all,
and it returns almost nothing.** Management owns every requirement→execution transformation.
Firmware receives a *pointer* to an already-derived stage, pulls that stage over HTTP, drives
valves and a blower, and posts back **deflection triples and nothing else**. No pressure, no
duration, no cycle count, no timestamp and no pass/fail ever travels firmware→Management.

Ranked by consequence for the Airtable integration:

1. **Programme derivation is 100% Management-owned — Model B, via a callback pull** (§6).
   The MQTT `start` command carries no physical quantity whatsoever. Firmware then `GET`s the
   derived stage. Confirmed to full precision against production: project 78 (DP 75/75 PSF)
   → cyclic stage 4 → `high=75.0, low=22.5, cycles=50`, exactly
   `75 × HIGH[4]=1.0`, `75 × LOW[4]=0.3`, `CYCLE_COUNT[4]=50`.

2. **`recovery` is not a measurement. It is a config constant.** All **609** real
   firmware-written deflection rows carry `recovery = 60` — verbatim `recovery_time` from the
   rig config. Cyclic tests post `recovery = 0` unconditionally. This closes contract §10.27's
   `recovery` limb outright (§12.4).

3. **The implausible deflections are real, and the defect is in the SICK gateway, not the
   firmware.** The gateway takes the first two bytes of an IO-Link process-data array as a
   big-endian unsigned 16-bit word, **asserts by comment that it is millimetres**, applies no
   device scale factor, and multiplies by 0.0393701. The DB extremes (±1288.86) decode to raw
   words of ≈±32700 — the signed-int16 full-scale boundary (32767). Firmware performs *zero*
   deflection arithmetic; it is a pass-through (§12).

4. **Nobody owns Passed/Failed.** `test_results.result` is written by **no endpoint in
   report-api** — the two trial-creation routes hardcode `result=None`, and
   `PUT /test-results/{id}` accepts only `note` and `image`. All **129** real
   (SICK-era) trials have `result = NULL`. The 275 populated values are seed data (§8).

5. **473 of 1082 deflection rows and every populated `result` are synthetic seed data.**
   `populate_db.py` generates gauge names `"Gauge 1".."Gauge 4"`, `random.uniform(0.5, 15.0)`
   deflections, `random.choice([True,True,False])` results, and
   `recovery = max_def − perm_def`. The two gauge-naming schemes in production are therefore
   **two provenances, not two rig generations** — and they disagree on what `recovery` *means*
   (inches vs seconds) in one column (§12.5).

6. **Cyclic cycles are open-loop and time-driven, not pressure-driven.** Every pressure check
   in the cycle loop is commented out and replaced by `if True: … time.sleep(1.0)`. Measured in
   production: 50 cycles in 101.07 s = **2.021 s/cycle**, matching the two 1.0 s sleeps exactly.
   `low_pressure` has **no effect on execution** beyond `max(abs(high), abs(low))` in the
   initial ramp (§6.2).

7. **Static tests have no automatic pressure control at all.** `HoldingTimeState` waits for
   `abs(sensor) > abs(setpoint)` and never commands the VFD. The operator ramps the blower by
   hand from a browser slider that publishes MQTT directly. There is no timeout — an
   unreachable setpoint blocks the state machine forever (§6.1, §9.3).

8. **Air and water infiltration are not firmware features.** Firmware has no infiltration
   state, no flow reading in the execution path and no leakage output. The *water* stage the rig
   actually runs is a **900-second static hold at 0.15 × inward design pressure**, filed in
   `static_tests`. The `infiltration_tests` table is a parallel, manually-entered record with
   no firmware involvement (§6.3).

9. **Impact/missile is entirely outside firmware** — 39 tests / 114 shots, all operator-entered.
   It is also the *only* place a pass/fail is genuinely recorded (`shots.result`: 72 true /
   42 false) (§6.4, §8).

10. **The two production rigs are not running the same firmware, and `system-1` is
    misconfigured.** `states/idle.py` differs on `system-2` (missing the RELIEF guard — the
    valve-3 stuck-open fix never reached it). On `system-1`, `state_machine` and `valves_service`
    are bind-mounted on **`config1-site-b.json`** while `serial_service` uses `config1.json`:
    two different config files, live, in the same rig (§3.3).

11. **Deflection acquisition is currently down fleet-wide.** Both SICK masters have been
    unreachable since **2026-08-29 23:08** (45 861 consecutive failures, no success in the
    retained log). Any test run since then records `deflections: []` (§9.5).

**What this means for Airtable, in one line:** the requirements side is small and clean — we
need essentially **three numbers and one boolean** per specimen (§14.1). The results side is
the problem: **LabOS currently produces almost nothing worth exporting**, and the one thing it
does produce in volume — deflection — is not in a trustworthy unit (§14.3).

---

## 2. Investigation Scope and Safety

### 2.1 Nodes and runtime sources inspected

| Node | Reached | What was read |
|---|---|---|
| `system-1` | remote.it proxy, user `labadm` | 3 containers, deployed `/app` trees, both live configs, container device maps, serial + state-machine logs |
| `system-2` | remote.it proxy, user `labadm` | 4 containers, deployed `/app` trees, live config, logs |
| `management` | remote.it proxy, user `labadm` | 7 containers, `report-api` source, 2 SICK gateways + env, mosquitto config, UI bundle, `report_db` (SELECT-only) |
| local clone | `feature/labos-firmware-p3` | full firmware source, used only as a **comparison baseline** against deployed images |

### 2.2 Read-only guarantee

Every command is logged in `firmware-production-probe-2026-08-31.txt`. Only three classes were
used: container/image inspection, file reads, and `SELECT`-only SQL. Specifically **not** done:
no MQTT publish, no rig motion, no VFD or valve command, no test created or started, no
POST/PUT/PATCH/DELETE to `report-api`, no container restart/rebuild/deploy, no config edit, no
DB write, no migration, no `docker cp` into an app tree, no log clearing, no git operation
touching a worktree, and no temporary instrumentation.

The only writes were SELECT-only `.sql` files carried to `/tmp` on `management` and `/tmp`
inside the `db` container so `psql -f` could read them. No path under `/app`, no bind mount and
no image layer was touched.

### 2.3 Limitations — what this audit cannot establish

- **No test was executed**, so every dynamic claim rests on source plus the retained log of the
  **2026-08-26 16:48 cyclic run on `system-1`** (the most recent real execution) and the
  **2026-08-17 static run on `system-2`**.
- **Deflection gauges are offline** (§9.5), so no live gauge reading could be captured. The
  numeric mechanism behind the ±32700 raw words is therefore **UNKNOWN**, not merely unproven —
  it needs a controlled gauge test (§17, T4).
- `system-1`'s VFD is currently unpowered, so VFD behaviour is read from the 2026-08-26 log, not
  live.
- The `test` node is offline (since ~2026-07-24) and was not inspected. There is **no
  non-production rig**, which is itself the main blocker on §17.
- Failure modes (broker loss, power loss, duplicate command) were **not** provoked. They are
  derived from code and classified accordingly.

---

## 3. Production Fleet State

### 3.1 Inventory

| Node | Host | Role | Reachable | Branch / SHA | Containers | Deployed = repo? |
|---|---|---|---|---|---|---|
| `system-1` | `ifet4` | **production rig** | yes, up 5 d | image-baked; repo baseline `feature/labos-firmware-p3` | `state_machine` (img 2026-08-12), `serial_service` (2026-07-07), `valves_service` (2026-06-29) | **state_machine: identical.** `serial_service`: 1 file differs, cosmetic |
| `system-2` | `Sys2` | **production rig** + standalone turbo controller | yes, up 10 d | image-baked | `state_machine` (img 2026-06-26), `serial_service` (2026-07-09), `valves_service` (2026-06-26), `ifet-turbo-controller-valves_service` (2025-12-18) | **`states/idle.py` differs — behavioural** |
| `management` | `ManIfet` | **production** control node | yes, up 10 d | `latest` @ `90f9595`, worktree clean | `report-api`, `db` (postgres:13), `mosquitto`, `ui` (httpd), `pgadmin`, `sick_gateway-1`, `sick_gateway-2` | n/a (branch `latest`, not `main`) |
| `test` | — | non-production rig | **no** — offline since ~2026-07-24 | — | — | not inspected |

`alembic_version` = **`3a65a83e0463`** — unchanged, as expected by the deploy runbook.

### 3.2 Deployed-vs-repo divergence — CONFIRMED, and smaller than feared

Hashing every `.py` inside the running containers against the local clone gives a clean result:
**firmware execution logic is byte-identical across both production rigs and the repo, with
exactly two exceptions.**

**(a) `states/idle.py` on `system-2` — behavioural.**

```diff
--- src/state_machine/states/idle.py        (repo == system-1)
+++ system-2 deployed
-                    if not "FORCE" in valve['role'] and not "RELIEF" in valve['role']:
+                    if not "FORCE" in valve['role']:
```

This is the valve-3 stuck-open fix. On `system-2` it is **absent**: entering Idle force-opens
valves carrying the `RELIEF` role. `system-2` also restarts by cron daily (09:30 UTC / 05:30 EDT
— visible as a bare `Entering state: IdleState` every day in its log), so the pre-fix path
executes **once per day on a production rig**.

**(b) `vfd_handler/vfd_node.py` on `system-1` — cosmetic.** One removed `logger.info` line in
`publish_feedback`. No behavioural difference. `system-2` matches the repo.

### 3.3 `system-1` is running two different config files — CONFIRMED

| Container | Bind-mounted config | md5 |
|---|---|---|
| `state_machine` | `deployment/config/config1-site-b.json` | `ebf93e34…` |
| `valves_service` | `deployment/config/config1-site-b.json` | `ebf93e34…` |
| `serial_service` | `deployment/config/config1.json` | `47c84940…` |

On `system-2` all three mount `config2.json` (single md5 `6e7d1097…`).

`CLAUDE.md` states system-1 "bind-mounts `config1.json`". That is true **only of
`serial_service`**. The state machine and the valve driver are on the **site-b** config. The two
files disagree on facts that matter:

| Key | `config1.json` (serial) | `config1-site-b.json` (state machine + valves) |
|---|---|---|
| `serial.port` | `/dev/ttyUSB0` ✓ matches the mapped device | `/dev/ttyACM0` ✗ (harmless — state_machine never opens serial) |
| sensor `scale`/`unit` | `144` / `PSF` ✓ | absent (harmless — only `serial_service` reads them) |
| `vfd.address` | `12` ✓ | `5` (harmless — only `serial_service` talks Modbus) |
| valve `name`→`pin` | — | `1→15, 2→31, 3→35, 4→13` — **live, and this file owns it** |

Today the split is benign *by luck*: each service happens to read only the keys its own file has
right. But the valve→GPIO map and the valve **roles** — the things that decide which physical
valve opens for an inward vs outward test — are being taken from a config named for a different
site. Note the pin maps are transposed between the two rigs (`system-1`: 1→15, 4→13;
`system-2`: 1→13, 4→15), so this is not a copy that can be assumed equivalent.

**Not a finding about the integration contract; a finding about production hygiene.** Flagged
here because it is exactly the class of drift that makes a rig execute something other than what
Management asked for, and it is invisible from the repo.

### 3.4 Turbo is disabled in production data

`devices` contains exactly two rows, both `turbo_mode = f`, `turbo_slave = f`,
`turbo_charger = NULL`. Firmware sets `self.slave = api.get_device(id)['turbo_charger']`, so
`self.slave` is always `None` and **every turbo branch in the state machine is dead in
production**. Confirmed in the 2026-08-26 log: `GET /devices/1` returned
`{'name': 'IFET Test Chamber Alpha', 'id': 1, 'turbo_mode': False, 'turbo_slave': False, 'turbo_charger': None}`.

The standalone `ifet-turbo-controller` on `system-2` is therefore **not** driven by the state
machine on the path audited here. How valves 5/6 are actually commanded is **UNKNOWN** and out of
scope; it does not touch the Airtable boundary.

---

## 4. Actual System Boundary

The boundary is **two channels, not one**, and the direction of the *data* is the opposite of
what "Management sends a test to the rig" suggests.

```
Airtable requirements
        │  (not yet connected — nothing is deployed)
        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LabOS Management (node `management`)                                    │
│                                                                          │
│  React UI (httpd)  ──── HTTP ────►  report-api :8000  ────►  postgres    │
│        │                             (owns ALL derivation)   report_db   │
│        │ mqtt-over-websockets :8084                                      │
│        ▼                                                                 │
│  mosquitto :1883 / :8084   allow_anonymous true, no TLS                  │
└───────┬──────────────────────────────────────────────▲──────────────────┘
        │                                              │
   (1) MQTT  device{N}/command                    (2) HTTP  GET the derived stage
       payload = IDENTIFIERS ONLY                     GET /devices/{id}
       {command, mode, project_id,                    GET /projects/{p}/static-tests/{i}
        test_index, sensor_id,                        GET /projects/{p}/next-cyclic-test
        selectedSensors, custom_preset, test_id}
        │                                              │
        ▼                                              │
┌─────────────────────────────────────────────────────────────────────────┐
│ Firmware / Rig (`system-1`, `system-2`)                                 │
│                                                                          │
│  state_machine ──MQTT──► valves_service ──GPIO──► solenoid valves        │
│       │        ──MQTT──► serial_service ──Modbus RTU──► VFD (blower)     │
│       ◄─MQTT── serial_service  {device}/sensors/{addr}  pressure, PSF    │
│       ◄─MQTT── sick_gateway    sick/sensors/{gauge}     deflection       │
│       ──MQTT─► sick/assign/{gauge} , sick/release/{gauge}                │
└───────┬─────────────────────────────────────────────────────────────────┘
        │
   (3) HTTP POST  the ONLY result channel
       POST /projects/{p}/{static_tests|cyclic-tests}/{i}/trials
       payload = {"deflections":[{deflection_gauge, max_deflection,
                                  permanent_deflection, recovery}]}
       ── no pressure, no duration, no cycles, no timestamps, no pass/fail ──
        │
        ▼
   report_db  →  Reports  →  (future) Airtable
```

**Deflection never passes through firmware arithmetic.** The SICK gateway runs on `management`,
polls the IO-Link masters over HTTP, and publishes already-converted values to MQTT. Firmware
stores the JSON verbatim and copies two of its fields into the HTTP POST. Physically the data
leaves `management`, crosses to the rig, and comes straight back.

### 4.1 Channel inventory

| # | Name | Direction | Transport | Payload | Ack / response | Source |
|---|---|---|---|---|---|---|
| 1 | `{device_id}/command` | Mgmt→FW | MQTT, QoS 0, not retained | JSON, see §5.1 | **none** | `state_machine.py:285` `on_message` |
| 2 | `{device_id}/emergency_stop` | Mgmt→FW | MQTT | any payload (ignored) | none | `state_machine.py:299` |
| 3 | `{device_id}/vfd/command` | Mgmt→FW **and** FW→FW | MQTT | `{"command","parameter"}` | none | `state_machine.py:279`, `vfd_node.py` `on_message` |
| 4 | `{device_id}/current_input` | Mgmt→FW | MQTT | opaque JSON | echoed to `initial_value` | `state_machine.py:311` |
| 5 | `{device_id}/sensors/{address}` | serial→SM | MQTT | bare float, 3 dp, PSF | none | `sensor_node.py:78` |
| 6 | `sick/sensors/{gauge}` | gateway→SM | MQTT | JSON, see §12.2 | none | `sick_mqtt_gateway.py` `poll_devices` |
| 7 | `sick/assign/{gauge}` / `sick/release/{gauge}` | FW→gateway | MQTT | `{"testing_system_id"}` / `"free"` | `assignment_status` topic | `initialize.py:22`, `recovery.py:58` |
| 8 | `{device_id}/valves/{name}` | SM→valves | MQTT | `0` \| `1` | `{device_id}/valves/status` | `initialize.py`, `relief.py`, `stopping.py` |
| 9 | `GET /devices/{id}` | FW→Mgmt | HTTP | — | `{name,id,turbo_mode,turbo_slave,turbo_charger}` | `api/api.py:16` |
| 10 | `GET /projects/{p}/static-tests/{i}` | FW→Mgmt | HTTP | — | `StaticTestSchema` | `api/api.py:10` |
| 11 | `GET /projects/{p}/next-cyclic-test` | FW→Mgmt | HTTP | — | `CyclicTestSchema` | `api/api.py:22` |
| 12 | `PUT …/cyclic_tests/{i}/start` | FW→Mgmt | HTTP | — | sets `resume=true` | `api/api.py:48` |
| 13 | `PUT …/cyclic_tests/{i}/update_status` | FW→Mgmt | HTTP | `{"current_cycle"}` | echo | `api/api.py:80` |
| 14 | `POST …/{static_tests\|cyclic-tests}/{i}/trials` | FW→Mgmt | HTTP | `{"deflections":[…]}` | `{id, trial_number, deflections, image_path, note}` | `api/api.py:28,56` |
| 15 | `{device_id}/status`, `/current_test_index`, `/notify` | FW→Mgmt | MQTT, 0.3 s | status string / int | none | `state_machine.py:255,580` |
| 16 | `ifet/firmware/{device_id}/owned-sensors` | FW→broker | MQTT, QoS 1, **retained** | JSON list | — | `sensor_ownership.py` |

**Endpoints report-api exposes that firmware never calls:**
`PUT …/static_tests/{i}/finish`, `PUT …/cyclic_tests/{i}/finish`, `PUT …/cyclic_tests/{i}/reset`,
`PUT /test-results/{id}`. Stage completion and note/photo attachment are **operator actions**
(§6.5, §8).

### 4.2 Transport-level properties

- **No authentication anywhere.** `mosquitto.conf`: `allow_anonymous true`, no TLS, listeners
  1883 (mqtt) and 8084 (websockets). `report-api` has no auth on any route. Any host on the LAN
  can publish `device1/command` and start a physical test. *(Observation, not a request to change
  anything.)*
- **No acknowledgement on the command channel.** MQTT QoS 0, not retained, no reply topic.
  Management cannot tell whether a `start` was received; it can only watch
  `{device_id}/status` change.
- **No request identity, no idempotency, no deduplication** — anywhere. See §9.7.
- **URL casing is inconsistent but functional**: firmware `GET`s `/static-tests/{i}` (hyphen,
  no trailing slash) against a route declared `/static-tests/{i}/`, and `POST`s to
  `/static_tests/{i}/trials` (underscore). Both resolve — FastAPI 307-redirects the GET and
  `requests` follows it. Fragile, not broken.

---

## 5. Management → Firmware Inputs

### 5.1 The `start` command — verbatim from production

`system-1`, 2026-08-26 16:48:26,184, topic `device1/command`:

```json
{"command": "start", "mode": "cyclic", "custom_preset": "preset",
 "sensor_id": "5", "test_id": null, "project_id": 78,
 "selectedSensors": [], "test_index": 4}
```

**Not one physical quantity is present.** No pressure, no duration, no cycle count, no
direction. Everything physical is fetched in step (2).

| Field | Type | Required | Validation | Firmware use | Notes |
|---|---|---|---|---|---|
| `command` | str | **yes** | `KeyError` if absent → caught, logged, message dropped | dispatch: `start`, `slave_turn_off`; internal: `turn_on`, `hold`, `automatic`, `relief`, `turn_off`, `recovery`, `idle` | not an enum; unknown value silently ignored |
| `mode` | str | **yes** | none | `manual` → static path; `cyclic` → cyclic path | **any other value silently does nothing** — no else branch |
| `project_id` | int | **yes** | none | path param on every API call | |
| `test_index` | int | yes (static) | none | static: the stage to fetch. **cyclic: ignored** | see §6.2 |
| `sensor_id` | str | **yes** | none | key into `sensors_values` — the **control pressure sensor**, by Modbus address | `KeyError` → `on_enter` raises inside the state thread |
| `selectedSensors` | list[str] | yes | none | deflection gauges to assign; `[]` is legal and yields no deflection data | |
| `custom_preset` | str | no | **never read** | — | dead field; the branch that used it is commented out |
| `test_id` | int\|null | no | **never read** | — | dead field |

**Error behaviour:** `on_message` wraps everything in `try/except`; a malformed payload is
logged and dropped with no reply. `mode` values other than `manual`/`cyclic` fall through to
nothing — the rig stays Idle and Management is never told why.

### 5.2 The derived stage — pulled by firmware

**Static** — `GET /projects/{p}/static-tests/{i}` → `StaticTestSchema`:

| Field | Type | Unit | Firmware use |
|---|---|---|---|
| `pressure` | float | **PSF** | `setpoint = pressure × (+1 outward / −1 inward)` — **sign then discarded**, §11.3 |
| `duration` | int | **seconds** | `holdtime`; `HoldingTimeState` counts `duration × 10` × 0.1 s |
| `type` | str | — | `"inward"` \| `"outward"` → `action = 'positive' if outward else 'negative'` |
| `index` | int | — | `test_index_wanted`, used in the result POST path |
| `finished`, `preset`, `trials`, `id` | — | — | **never read by firmware** |

**Cyclic** — `GET /projects/{p}/next-cyclic-test` → `CyclicTestSchema`. Verbatim from production:

```json
{"type": "outward", "cycles": 50, "low_pressure": 22.5, "high_pressure": 75.0,
 "finished": false, "index": 4, "resume": false, "current_cycle": 0,
 "trials": [], "preset": true}
```

| Field | Type | Unit | Firmware use |
|---|---|---|---|
| `high_pressure` | float | **PSF** | `positive_setpoint = high × (−1 outward / +1 inward)` → ramp target via `max(abs)` |
| `low_pressure` | float | **PSF** | `negative_setpoint`; **only ever reaches `max(abs(pos), abs(neg))`** — no per-cycle effect |
| `cycles` | int | count | `cycle_counter`, the loop bound |
| `current_cycle` | int | count | `cycle_index`, the loop start — the resume seam |
| `type` | str | — | direction, as static |
| `index` | int | — | `test_index_wanted` — **overrides the MQTT `test_index`** |
| `resume`, `finished`, `preset`, `trials` | — | — | **never read by firmware** |

### 5.3 Complete inventory of firmware-executable inputs

Every value that can influence physical execution. `Source` provenance is the column that
matters for the integration.

| Input | Test type | Type | Unit | Req? | Source | Derived where? | Firmware use | Validation |
|---|---|---|---|---|---|---|---|---|
| `pressure` | static | float | PSF | yes | **Management DB** | Mgmt: `outward\|inward DP × [0.75,0.75,1,1,1.5,1.5][j]` | setpoint magnitude | **none** |
| `duration` | static | int | s | yes | Management DB | Mgmt: constant `30` (preset); operator (ad-hoc) | hold loop | **none** |
| `type` | static, cyclic | str | — | yes | Management DB | Mgmt: `j%2` / `i<4` | valve role selection | **none** — unknown value ⇒ `negative` |
| `high_pressure` | cyclic | float | PSF | yes | Management DB | Mgmt: `DP × [0.5,0.6,0.8,1,1,0.8,0.6,0.5][i]` | ramp target | **none** |
| `low_pressure` | cyclic | float | PSF | yes | Management DB | Mgmt: `DP × [0.2,0,0.5,0.3,0.3,0.5,0,0.2][i]` | **ramp target only** | **none** |
| `cycles` | cyclic | int | count | yes | Management DB | Mgmt: `[3500,300,600,100,50,1050,50,3350][i]` | loop bound | **none** |
| `current_cycle` | cyclic | int | count | yes | Management DB | firmware writes it back | loop start index | **none** |
| `index` | both | int | — | yes | Management DB | Mgmt (`+1` shift if water stage) | result routing | **none** |
| `sensor_id` | both | str | — | yes | **operator** (UI) | — | control-sensor selection, by Modbus address | **none** — bad value ⇒ `KeyError` |
| `selectedSensors` | both | list | — | yes | **operator** (UI) | — | which gauges to assign/record | none; `[]` legal |
| `mode` | both | str | — | yes | **operator** (UI) | — | static vs cyclic path | none; unknown ⇒ silent no-op |
| `project_id` | both | int | — | yes | operator (UI) | — | API routing | none |
| VFD frequency | **static** | float | **Hz** | — | **operator** (browser slider → MQTT) | — | **the entire pressure control loop for static** | **none, no bound** |
| `recovery_time` | both | int | s | no | **firmware config** | — | post-test hold; **and posted as the `recovery` result** | `int()` cast |
| `cyclic_skip_recovery` | cyclic | bool | — | no | firmware config | — | bypass RecoveryState ⇒ `recovery = 0` | `bool()` cast |
| sensor `scale` | both | float | — | no | firmware config | — | PSI→PSF (`×144`) | `float()`, default `1` |
| sensor `address` | both | int | — | yes | firmware config | — | Modbus slave id | `int()` |
| `vfd.address` | both | str | — | yes | firmware config | — | Modbus slave id | `int()` |
| valve `role[]` | both | list | — | yes | firmware config | — | **which valve opens for which direction** | **none** |
| valve `pin` | both | int | — | yes | firmware config | — | GPIO | none |
| `turbo.*` | both | obj | — | no | firmware config + `devices.turbo_charger` | Mgmt | dead in production (§3.4) | none |
| gauge zero offset | both | int | raw counts | — | **sensor-derived**, at assign | SICK gateway | deflection datum | none |
| `emergency_stop` | both | — | — | — | operator (UI) | — | `force_stop = True` | none |
| `custom_preset`, `test_id`, `toggleBtn`, `active`, `preset`, `resume` | — | — | — | — | — | — | **never read** | — |

**Provenance summary:** every *physical* input is **Management-derived from the design-pressure
pair**. Everything else is either **firmware configuration** (units, addresses, valve roles,
recovery time) or **operator-entered** (mode, control sensor, gauge selection, and — for static —
the blower frequency itself). **Nothing physical is Airtable-originated today**, because nothing
is deployed.

**There is no validation anywhere on the wire.** Pydantic enforces types
(`pressure: float`, `duration: int`, `cycles: int`) and nothing else — no range, no sign, no
unit, no cross-field check. A `pressure` of 9 PSF and a `pressure` of 900 PSF are equally
acceptable to every layer. This is precisely why contract §10.19 (the Airtable extraction shift)
is unrepairable downstream: **there is no layer in LabOS that could reject a plausible-but-wrong
requirement value.**

---

## 6. Test Programme Ownership and Derivation

### 6.0 The answer: Model B, delivered by callback pull

Neither A nor C. **Management derives the complete execution stage and stores it; firmware pulls
it and executes it verbatim.** The unusual part is the *transport*: the trigger is a push (MQTT,
identifiers only) and the data is a pull (HTTP, firmware-initiated).

```
Model B (actual):
  Management  ──MQTT {project_id, test_index, mode, sensor_id}──►  Firmware
  Management  ◄──HTTP GET the derived stage───────────────────────  Firmware
  Management  ──HTTP response {pressure|high/low, duration|cycles, type}──►  Firmware
                                                                     └─► Rig
```

**Firmware performs exactly one arithmetic operation on any requirement value:** a sign
multiplication that is then discarded by `abs()` (§11.3). It performs **no** factor lookup, no
stage generation, no unit conversion of a requirement, and no result computation.

The single generator is `report-api` `POST /devices/{device_id}/projects/`
(`app/main.py:124`), which on project creation writes all 14 stages at once:

```python
for i in range(8):                                   # cyclic
    h, l, c = CyclicTestPressureCalculator.get_cylcic_test_data(
        inward_design_pressure if i < 4 else outward_design_pressure, i)
    type = "inward" if i < 4 else "outward"

for j in range(6):                                   # static
    p, d = StaticTestPressureCalculator.get_static_test_data(
        outward_design_pressure if j % 2 else inward_design_pressure, j)
    type  = "outward" if j % 2 else "inward"
    index = j + (1 if project.has_water_infiltration and j > 3 else 0)

if project.has_water_infiltration:                   # the water stage
    pressure = inward_design_pressure * 0.15
    duration = 900
    type     = "inward"
    index    = 4
```

with

```python
StaticTestPressureCalculator.STATIC_PRESSURE_FACTOR = [0.75, 0.75, 1, 1, 1.5, 1.5]
    get_static_test_data → (design_load * factor, 30)      # 30 s, hardcoded

CyclicTestPressureCalculator.HIGH_PRESSURE_FACTORS = [0.5, 0.6, 0.8, 1.0, 1.0, 0.8, 0.6, 0.5]
CyclicTestPressureCalculator.LOW_PRESSURE_FACTORS  = [0.2, 0.0, 0.5, 0.3, 0.3, 0.5, 0.0, 0.2]
CyclicTestPressureCalculator.CYCLE_COUNT           = [3500, 300, 600, 100, 50, 1050, 50, 3350]
```

**Production validation, project 78 (`inward_design_pressure = 75`, `outward = 75` PSF):**

| Stage | Expected | Actual in DB | |
|---|---|---|---|
| static 0–5 | `75 × [.75,.75,1,1,1.5,1.5]` = 56.25, 56.25, 75, 75, 112.5, 112.5; alternating inward/outward from **inward**; `duration = 30` | 56.25 in, 56.25 out, 75 in, 75 out, 112.5 in, 112.5 out; all `duration = 30` | ✅ exact |
| cyclic 0–7 high | `75 × [.5,.6,.8,1,1,.8,.6,.5]` = 37.5, 45, 60, 75, 75, 60, 45, 37.5 | 37.5, 45, 60, 75, 75, 60, 45, 37.5 | ✅ exact |
| cyclic 0–7 low | `75 × [.2,0,.5,.3,.3,.5,0,.2]` = 15, 0, 37.5, 22.5, 22.5, 37.5, 0, 15 | 15, 0, 37.5, 22.5, 22.5, 37.5, 0, 15 | ✅ exact |
| cyclic cycles | 3500, 300, 600, 100, 50, 1050, 50, 3350 | identical | ✅ exact |
| cyclic direction | 0–3 inward, 4–7 outward | 0–3 inward, 4–7 outward | ✅ exact |

And end-to-end through the boundary: the 2026-08-26 log shows firmware receiving
`high_pressure: 75.0, low_pressure: 22.5, cycles: 50` for `index: 4` — the exact derivation
output. **CONFIRMED from production, at full precision, across all three layers.**

> **Correction to a standing assumption.** Our management-side note said cyclic presets
> *alternate* inward/outward like static. They do not: **cyclic is 0–3 inward then 4–7 outward**
> (`i < 4`). Static *is* alternating (`j % 2`). Two different rules — worth getting right, since
> the direction determines which physical valve opens.

**Preset vs ad-hoc, production-wide:** ad-hoc stages are rare but real —
static **10 of 501** (2.0%, 6 projects), cyclic **2 of 626** (0.3%, 2 projects). Static stage
counts per project: 6 stages × 50 projects, 7 × 25 (the water-infiltration projects), 8 × 1,
9 × 2.

### 6.1 Static test execution contract

```
business requirement:  inward/outward design pressure (PSF)   [Airtable → Management]
        ↓ OWNER: Management (report-api, project creation)
management repr.:      static_tests row {pressure PSF, duration 30 s, type, index, pressure_factor}
        ↓ OWNER: Management (no further derivation)
firmware payload:      GET response, verbatim
        ↓ OWNER: Firmware (sign multiply, then discarded)
hardware control var:  action ∈ {positive, negative} → valve roles
                       |setpoint| PSF                → threshold on the control sensor
                       holdtime s                    → countdown
                       VFD frequency Hz              → OWNER: **the operator**
```

**Semantics, as actually implemented:**

| Concept | Reality | Owner |
|---|---|---|
| target pressure | `pressure` PSF, magnitude only | Management |
| direction | `type` → `action`; `outward` ⇒ `action='positive'` ⇒ valves with role `POSITIVE` | Management |
| pressure sign | computed, then **discarded** by `abs()` — inert | — |
| pressure unit | **PSF** at every layer above the sensor | firmware config (`scale: 144`) |
| hold duration | `duration × 10` iterations of `time.sleep(0.1)` ⇒ **seconds** | Management |
| stage order | not enforced for static — the ordering check is **commented out** in `finish_static_test` | nobody |
| start | operator publishes MQTT `start` | operator |
| **reaching the setpoint** | **`while abs(sensor) > abs(setpoint)` is false: spin.** No VFD command is ever issued. The loop assigns `self.freq = self.machine.freq_command` to a variable that is never read — dead code. **The blower is ramped by the operator's browser slider.** No timeout (commented out) ⇒ blocks forever if the setpoint is unreachable | **operator** |
| completion | hold countdown expires → Relief → Stopping → Recovery → Idle | firmware |
| abort | `force_stop` — only from MQTT `emergency_stop` or broker disconnect | operator / transport |
| **actual measured pressure** | **never reported, never persisted, anywhere** | — |
| **max achieved pressure** | **never computed** | — |
| deflection | pass-through from the SICK gateway | **gateway** |
| permanent set | gateway's `latest_value` = last sample while assigned | **gateway** |
| pass/fail | **never written by anything** (§8) | nobody |

**State trace (source-derived; matches the `system-2` 2026-08-17 log):**

```
Idle ──start(mode=manual)──► [GET /devices, GET /static-tests/{i}]
  → InitializeState      publish valve settings for `action`; sick/assign each gauge
                         on_exit: block until valves/status matches (no timeout)
  → StartVDFState        set_vfd_speed(0); set_vfd_state("start")
                         on_exit: block until vdf_feedback == 0, 90 s timeout → TimeoutError
  → HoldingTimeState     on_enter: spin until |sensor| > |setpoint|   ← operator drives VFD
                         on_exit: countdown `duration` seconds
  → ReliefValvesState    open ACTIVE valves; block until valve_status all truthy
  → StoppingState        set RELIEF valves; loop set_vfd_speed(0)+stop until vdf_feedback == 0
  → RecoveryState        hold `recovery_time` (60 s)
                         on_exit: POST /trials {deflections, recovery=recovery_time}; notify()
  → Idle                 release gauges, clear retained ownership
```

### 6.2 Cyclic test execution contract

```
business requirement:  inward/outward design pressure (PSF)
        ↓ OWNER: Management — factors + cycle counts, 8 stages, 0–3 inward / 4–7 outward
management repr.:      cyclic_tests row {high_pressure, low_pressure, cycles, type, current_cycle}
        ↓ OWNER: Firmware
hardware control var:  ramp target = max(|high|, |low|) PSF   → closed-loop VFD ramp
                       cycles                                  → loop bound
                       action                                  → which RELEASE valve toggles
                       ** per-cycle pressure: NOT CONTROLLED **
```

| Concept | Reality | Owner |
|---|---|---|
| high pressure | `high_pressure` PSF; reaches execution **only** as `max(abs(high), abs(low))` | Management |
| low pressure | `low_pressure` PSF; **no per-cycle effect** — every check using it is commented out | Management (inert) |
| direction | `type` → `action`; selects `POSITIVE_RELEASE` vs `NEGATIVE_RELEASE` | Management |
| cycle count | `cycles`, `for i in range(cycle_index, cycle_counter)` | Management |
| **cycle progression** | **fixed 2.0 s per cycle**: toggle RELEASE valve → `time.sleep(1.0)` → toggle back → `time.sleep(1.0)`. Pressure is never checked | firmware (open-loop) |
| ramp | **genuine closed loop**: step 5/3/1 Hz by `abs_error`, gated on `freq_command − vdf_feedback < 0.3`, exit at `error ≥ −0.15 × setpoint` ⇒ **≈85% of target** | firmware |
| pressure unit | PSF | firmware config |
| start | MQTT `start`, then `PUT …/start` sets `resume = true` | operator / Management |
| progress | `PUT …/update_status {current_cycle: i}` **before** cycle *i* runs ⇒ maxes at `cycles − 1` | firmware |
| completion condition | loop exhausts. **`finished` is never set by firmware** | operator |
| abort | `force_stop` → `return` from the loop mid-test; **no trial is posted** | operator / transport |
| resume | **dead code**: `cyclic_resume` is only ever assigned `False`; the branch that set it is commented out. The `current_cycle` seam exists in Management but firmware cannot re-enter it | — |

**Production timing proof of the open loop** (`system-1`, 2026-08-26, `cycles = 50`):

| Phase | Window | Duration |
|---|---|---|
| ramp (`AutomaticCyclingState.on_enter`) | 16:48:26.333 → 16:48:53.390 | 27.06 s |
| **50 cycles (`on_exit`)** | 16:48:53.407 → 16:50:34.481 | **101.07 s ⇒ 2.021 s/cycle** |
| VFD coast-down (`StoppingState`) | 16:50:34.494 → 16:50:53.533 | 19.04 s |
| trial POST response | 16:50:53.589 | — |

2.021 s/cycle against the two coded `time.sleep(1.0)` calls: **CONFIRMED, the cycle loop is
time-driven and pressure-independent.** The ramp trace in the same log shows the closed loop
working as designed (`freq_command` 0→5→10→…→35 Hz, `vdf_feedback` following: 0.0, 1.92, 4.73,
5.78, 8.78, 10.0, 11.36, 14.34, 15.0, …) with the control sensor rising 0.278 → 56.044 PSF
against a 75 PSF target — i.e. the run was still ramping toward ≈85% when the exit condition
fired.

Scale consequence: stage 0 (3500 cycles) at 2.02 s/cycle ≈ **1 h 58 m**; the full 9000-cycle
programme ≈ **5 h**.

**Preset vs ad-hoc at the boundary — they are indistinguishable.** An ad-hoc cyclic stage is a
`cyclic_tests` row with `preset = false` and operator-supplied `high/low/cycles/type`. Firmware
receives the identical `CyclicTestSchema` and **never reads `preset`**. Both production ad-hoc
rows sit at `index = 8`, i.e. appended after the eight presets:

| project | index | type | cycles | low | high | preset |
|---|---|---|---|---|---|---|
| 27 | 8 | outward | 500 | 20 | 65 | false |
| 45 | 8 | inward | 6 | 10 | 30 | false |

Ad-hoc **static** stages carry `pressure_factor = ''` (empty) where presets carry
`'Structural Pressure'` — that empty string is the only marker distinguishing them in the
static table, and firmware never reads it either.

**Stage ordering *is* enforced for cyclic** (unlike static): `PUT …/start` and
`update_status` both refuse if any lower-index cyclic stage is unfinished, and `start` refuses
an already-finished stage. Those are the only real guards in the whole contract.

### 6.3 Air / Water Infiltration contract

**Firmware has no infiltration capability.** No infiltration state, no leakage measurement, no
flow reading in the execution path, no infiltration API call. There is a `flow` sensor type in
`serial_service`, but:

- it is configured **only on `system-1`** (`{"name":"Flow","address":11,"type":"flow","active":false}`);
- `active: false` does **not** gate polling (`sensor_node.add_sensor` ignores it — a
  `CLAUDE.md` gotcha, re-confirmed), so it *is* polled and publishes `device1/sensors/11`;
- it read **`0.0` throughout** the 2026-08-26 test;
- its `calc()` uses `self.P = 0` — the MQTT subscription that would populate ambient pressure,
  temperature and humidity is **entirely commented out** — leaving hardcoded `phi = 0.66`,
  `T = 87`, `P = 0`, with `T` used as Kelvin in one term and Celsius in another. The output is
  not a physically meaningful flow rate.
- The state machine never reads it for any control or result purpose.

**What actually happens instead:**

| "Infiltration" | Where it lives | How it is produced |
|---|---|---|
| **Water** (the stage a rig runs) | **`static_tests`**, index 4, `duration = 900` s, `pressure = 0.15 × inward_design_pressure`, `type = inward`, `preset = true`, `pressure_factor = 'Structural Pressure'` | Management, at project creation, iff `has_water_infiltration` |
| **`infiltration_tests` table** | separate table, `{type, pressure, duration, leakage}` | **manual entry only** — no endpoint firmware calls, no firmware write path |

The water stage is executed by firmware as an ordinary `mode: manual` static test: a 900-second
hold at 0.15 × IDP. **Leakage is not measured by firmware and never crosses the boundary.**

Production check on the 0.15 rule — exact, across every 900 s stage:

| project | pressure | inward DP | ratio |
|---|---|---|---|
| 29 | 10.5 | 70 | 0.1500 |
| 31 | 10.5 | 70 | 0.1500 |
| 35 | 12.75 | 85 | 0.1500 |
| 36 | 18 | 120 | 0.1500 |
| 41 | 15 | 100 | 0.1500 |
| 54 | 7.5 | 50 | 0.1500 |

**`has_water_infiltration` is an input to project creation that is never stored.** `models.py`
`Project` has no such column. It can only be recovered *post hoc* by detecting a 900 s static
stage. For Airtable this is a genuine requirement field that must cross the boundary (§14.1).

**Duration units — settled, against the documentation.** `infiltration_tests.duration` in
production ranges **321.30 → 1691.60** with full float mantissas
(e.g. `1339.0422327136741`, `1486.1222146541547`). As seconds that is 5–28 minutes: plausible.
As minutes it would be 5–28 **hours**: not. **Duration is seconds — CONFIRMED**, and the old
"minutes" annotation is wrong.

**But treat these 37 rows as suspect data, not measurements.** The full-mantissa floats across
`pressure` (25.149571252862664), `duration` and `leakage` (0.25247583776106086) are the
signature of `random.uniform()`, matching the seed-data pattern proven in §12.5. 13 Air /
24 Water rows, no firmware write path, and values that no instrument would produce.
**STRONGLY INDICATED: `infiltration_tests` is seeded demo data.** Do not export it (§14.3).

### 6.4 Impact / missile tests

**Firmware does not participate at all.** No missile state, no shot handling, no velocity or
area input, no MQTT topic, no API call. `state_machine` contains no reference to impact.

| Item | Where | Owner | Automated? |
|---|---|---|---|
| missile class / type | `missile_impact_tests.missile` (str) | operator | manual |
| missile weight | `missile_impact_tests.missile_weight` (float, unit **undeclared** — likely kg or lb, **UNKNOWN**) | operator | manual |
| number of impacts | implicit: `count(shots)` | operator | manual |
| shot number | implicit: row order; **no explicit column** | operator | manual |
| velocity | `shots.velocity` (float, unit **undeclared**, **UNKNOWN**) | operator | manual |
| area | `shots.area` (float, unit **undeclared**, **UNKNOWN**) | operator | manual |
| **result** | **`shots.result` (bool, NOT NULL)** | **operator** | manual |
| note | `shots.note` (str, NOT NULL) | operator | manual |

Production: **39 missile tests, 114 shots**, `result` = **72 true / 42 false**.

Two things follow. First, impact is **the only test type in LabOS where a pass/fail is actually
recorded** — and it is recorded per shot, by a human. Second, `velocity`, `area` and
`missile_weight` have **no unit declared in the schema, the API, or the code**. Those units are
genuinely unknown and must be established with the lab before any export (§16).

### 6.5 Who advances a stage

Nobody in firmware. `create_static_test_trial` and `create_cyclic_test_trial` do **not** set
`finished`; the cyclic route only clears `resume`. The `PUT …/finish` endpoints exist and
**firmware never calls them**.

Consequence, visible in production: project 78 cyclic stage 4 shows
`finished = false, current_cycle = 49` after a run that completed all 50 cycles on 2026-08-26.
`GET /next-cyclic-test` returns "the first unfinished stage by index", so it would hand the rig
**that same stage again**. Stage advancement is an explicit operator action in the UI.

Note also: `current_cycle = 49` for a 50-cycle stage that finished. Because
`update_status` is called with `i` *before* cycle `i` executes, `current_cycle` maxes at
`cycles − 1`. **Management cannot distinguish "completed all 50" from "aborted after 49" from
this field.**

---

## 7. Firmware → Management Outputs

**The complete inventory. It is four fields.**

`POST /projects/{p}/{static_tests|cyclic-tests}/{i}/trials`

```json
{"deflections": [{"deflection_gauge": "1-1", "max_deflection": 0.42,
                  "permanent_deflection": 0.07, "recovery": 60}]}
```

Wire schema (`schema.py`): `StaticTestResultCreateSchema` / `CyclicTestResultCreateSchema` have
**exactly one field**, `deflections: List[DeflectionCreateSchema]`, and
`DeflectionCreateSchema` is `{deflection_gauge: str, max_deflection: float,
permanent_deflection: float, recovery: float}` — all required, no bounds, no unit field.

| Output | Type | Unit | Produced by | Meaning | Persisted where? |
|---|---|---|---|---|---|
| `deflection_gauge` | str | — | **operator** (`selectedSensors`) → gateway id | which gauge; `1-1`…`2-8` from the gateway config | `deflections.deflection_gauge` |
| `max_deflection` | float | **raw IO-Link counts × 0.0393701, labelled inches** (§12) | **SICK gateway** | greatest-magnitude excursion from the assign-time zero, sign preserved (`abs(v) > abs(max)`) | `deflections.max_deflection` |
| `permanent_deflection` | float | same | **SICK gateway** | **the last sample taken while assigned** — not a settled post-recovery reading | `deflections.permanent_deflection` |
| `recovery` | float | **seconds** (static) / literal `0` (cyclic) | **firmware config** | `recovery_time`. **Not a measurement** | `deflections.recovery` |
| `current_cycle` | int | count | firmware | progress; maxes at `cycles − 1` | `cyclic_tests.current_cycle` |
| `resume = true` | bool | — | Management (on firmware's `PUT …/start`) | "a run has begun" | `cyclic_tests.resume` |
| `{device_id}/status` | str | — | firmware | free-text state label (below) | **nowhere** — MQTT only, not retained |
| `{device_id}/current_test_index` | int | — | firmware | current stage | **nowhere** |
| `{device_id}/notify` | str | — | firmware | "refresh the UI" | **nowhere** |

**Everything the report structure asked about that does not exist:**

| Requested output | Status |
|---|---|
| actual pressure, maximum pressure, low/high achieved | **NOT PRODUCED.** Never computed, never sent, no column exists |
| cycles requested / cycles completed | requested: only in `cyclic_tests.cycles` (the plan). **Completed: NOT PRODUCED** |
| duration (actual) | **NOT PRODUCED** |
| timestamps (start / end) | **NOT PRODUCED.** No datetime column on `test_results` at all |
| sensor / gauge measurements | only the three deflection numbers; **no pressure trace is retained** |
| max deflection, permanent deflection | produced — units unverified (§12) |
| recovery | produced, but it is a **config constant**, not a measurement |
| leakage | **NOT PRODUCED** by firmware (§6.3) |
| missile / impact measurements | **NOT PRODUCED** by firmware (§6.4) |
| current status | MQTT only, ephemeral, free text |
| terminal status | **NOT PRODUCED** — `finished` is an operator action |
| abort information | **NOT PRODUCED.** An aborted test posts nothing at all (§9.4) |
| fault information | **NOT PRODUCED.** No fault topic, no fault field |
| result / pass-fail | **NOT PRODUCED** (§8) |

Production confirmation, the 2026-08-26 POST response at 16:50:53,589:

```json
{"deflections": [], "id": 637, "trial_number": 1, "image_path": null, "note": null}
```

`trial_number` is assigned by Management as `len(test.trials) + 1`. `deflections: []` because
the operator selected no gauges (`selectedSensors: []`). **That completed 50-cycle production
test is recorded as: one row, trial number 1, and nothing else.**

Production-wide: **637 trials, of which 348 (55%) have no deflection rows at all.**

---

## 8. Result / Pass-Fail Ownership

**Verdict: nobody owns it. In the current production system a rig-executed test has no
pass/fail, and no code path can give it one.**

Evidence chain:

1. `TestResult.result = Column(Boolean, nullable=True)` — the column exists.
2. Firmware's POST body cannot express it: `StaticTestResultCreateSchema` has only
   `deflections`.
3. Both trial-creation routes hardcode it: `result=None` (`main.py:389`, `main.py:561`).
4. `grep "\.result\b|result=|result =" main.py` returns **only** those two assignments plus
   read-only uses in the report renderers (lines 912, 947, 988, 1079, 1114, 1155).
5. `PUT /test-results/{id}` — the one route that updates a trial — accepts **`note` and
   `image` only**. It cannot set `result`.
6. Therefore **no endpoint in report-api ever writes `TestResult.result`.**

And the data agrees exactly:

| Trial's deflection provenance | `result = true` | `false` | `NULL` |
|---|---|---|---|
| has `Gauge N` rows (**seed data**) | 109 | 51 | **0** |
| has `1-1…2-8` rows (**real firmware**) | 0 | 0 | **129** |
| no deflections | 82 | 33 | 233 |

**Every real firmware-produced trial has `result = NULL`. Every populated `result` belongs to a
seed-data trial** (`populate_db.py:145`: `result=random.choice([True, True, False])` — and 109:51
is 2.14:1, matching that 2:1 distribution).

Per test type:

| Test type | Required-value owner | Actual-measurement owner | Comparison owner | Final-result owner |
|---|---|---|---|---|
| Static | Management (derived from DP) | **nobody** — pressure is never recorded; gateway owns deflection | **nobody** | **nobody** (`result` always NULL) |
| Cyclic | Management (derived from DP) | **nobody** — cycles-completed and pressure are never recorded | **nobody** | **nobody** |
| Water infiltration | Management (0.15 × IDP) | **nobody** — leakage not measured | **nobody** | **nobody** |
| Air infiltration | operator (manual row) | operator (manual `leakage`) | operator, offline | **not represented** |
| **Impact / missile** | operator | operator | **operator** | **operator** — `shots.result`, 72 true / 42 false |

So the only genuine pass/fail in LabOS is a human's per-shot judgement on missile tests. For
static and cyclic, the acceptance criterion (deflection limit) exists **nowhere** in the system:
not as a column, not as a config value, not in code.

**This is the biggest gap for Airtable.** The write contract's `Pass/Fail` field has no source.
Options are (a) Management computes it from a limit that must be supplied per specimen — a new
requirement input, and a LabOS-side build; or (b) it stays operator-entered and the integration
carries an operator judgement, not a computed verdict. This is a decision for the call, not
something to infer (§16, Q1).

---

## 9. State Machine and Failure Semantics

### 9.1 Actual states

The implementation uses its own vocabulary — eight states, no `Ready`, no `Completed`, no
`Fault`:

`IdleState`, `InitializeState`, `StartVDFState`, `HoldingTimeState`, `AutomaticCyclingState`,
`ReliefValvesState`, `StoppingState`, `RecoveryState`
(plus `ResumeState`, commented out of the registry).

`current_status` — the free-text label published to `{device_id}/status` every 0.3 s — is a
*different* and finer vocabulary: `initial`, `idle`, `valves configuration requested`,
`valves configuration approved`, `vfd reset`, `vfd started`, `zero_slider`, `tuning`, `tuned`,
`Holding {n}s`, `warming up`, `Cycle {n} High Stroke`, `Cycle {n} Low Stroke`,
`relief configuration requested`, `valves configured`, `colding down`,
`emergency: waiting for vdf to stop`, `vfd stopped`, `Closed Valves`, `Recovery {n}s`.

| State | Allowed transition | Trigger | Owner | Data emitted | Failure behaviour |
|---|---|---|---|---|---|
| Idle | → Initialize | MQTT `start` | operator | status; releases gauges, clears retained ownership | error sets `force_Stop` — **typo, no effect** |
| Initialize | → StartVDF | internal `turn_on` | firmware | valve commands, `sick/assign` | `on_exit` blocks until `valve_status` matches — **no timeout** |
| StartVDF | → HoldingTime (`hold`) or AutomaticCycling (`automatic`) | internal | firmware | `set_frequency 0`, `start` | 90 s timeout → raises `TimeoutError` inside the state thread; error sets `force_Stop` — **typo, no effect** |
| HoldingTime | → Relief | internal `relief` | firmware | status `tuning`/`Holding ns` | **no timeout** — blocks forever if setpoint unreachable |
| AutomaticCycling | → Relief | internal `relief` | firmware | VFD ramp, `PUT …/start`, `update_status` ×N | `force_stop` → `return` mid-loop, **no trial posted** |
| Relief | → Stopping | internal `turn_off` / `slave_turn_off` | firmware | valve commands | blocks on `all(valve_status)` — **no timeout** |
| Stopping | → Recovery, or → Idle if `cyclic_skip_recovery` | internal `recovery` | firmware | VFD stop loop; **POST /trials** in the skip path with `recovery = 0` | loop is `while not self.exit` — see §9.2 |
| Recovery | → Idle | internal `idle` | firmware | **POST /trials** with `recovery = recovery_time`; `notify()` | `force_stop` → **posts nothing** |

Both production rigs run `recovery_time = 60` and `cyclic_skip_recovery = true`. So:
**static → Recovery, posts `recovery = 60`; cyclic → skips Recovery, posts `recovery = 0`.**

### 9.2 What causes a start; what prevents one

**Start:** exactly one thing — an MQTT message on `{device_id}/command` with
`command: "start"`, handled only when `current_state` is `IdleState`.

**Prevented by:** being in any non-Idle state (the `isinstance` guard silently drops the event);
`mode` not in `{manual, cyclic}` (silent no-op); a `sensor_id` absent from `sensors_values`
(`KeyError`); for cyclic, `PUT …/start` returning 400 because a lower-index stage is unfinished —
though note that call happens **after the rig has already pressurised**, in
`AutomaticCyclingState.on_exit`, and its failure is not checked.

Nothing prevents a start based on: rig readiness, VFD reachability, gauge availability, whether
another test is already recorded, or whether the requested stage is already `finished`.

### 9.3 If Management disconnects

`on_disconnect` sets **`force_stop = True` and `exit = True`**. So a broker disconnection is an
**abort**, and it also terminates the process (`run()` returns, `app.py` calls `disconnect()`,
Docker's restart policy brings it back).

Two consequences, both **STRONGLY INDICATED** from code (not provoked):

- The physical test **stops** — it does not continue autonomously.
- `StoppingState.on_enter` loops `while not self.machine.exit`. With `exit` already `True`, that
  loop **breaks on the first check**, before confirming `vdf_feedback == 0`, and any
  `set_vfd_speed(0)` / `set_vfd_state("stop")` publish on a disconnected client is lost. So on a
  mid-test broker loss the VFD and valves may be **left in their test state** until the
  container restarts and `IdleState.on_enter` re-publishes safe positions. On `system-2` that
  Idle entry is the pre-fix `idle.py` that force-opens RELIEF valves (§3.2).

### 9.4 Abort, faults, and incomplete tests

- **Abort is issued** by publishing to `{device_id}/emergency_stop` (any payload). That calls
  `set_vfd_state('emergency_stop')` and sets `force_stop = True`. `VFDController.emergency_stop`
  (own thread) writes the stop register, then polls speed until it reads 0 — and `speed` is
  **never initialised before the loop** (`vfd_node.py:118-132`). So on a bus that is silent from
  the first read, `if speed == 0` raises an uncaught `UnboundLocalError` and **the
  emergency-stop thread dies**; if instead a first read succeeds non-zero and later reads fail,
  `speed` keeps the stale value and the loop **never exits**. Either way the confirmation that
  the VFD actually stopped is unreliable — and a silent bus is `system-1`'s current state.
- **`force_stop` has only two sources**: the `emergency_stop` topic and broker disconnect. There
  is no "stop" command on the command topic.
- **An aborted test posts nothing.** `RecoveryState.on_exit` skips the POST entirely when
  `force_stop`; `AutomaticCyclingState.on_exit` `return`s out of the cycle loop. Observed in
  production — `system-2`, 2026-08-17 14:15:05: `Entering state: RecoveryState` immediately
  followed by `WARNING - Holding time interrupted` and `Entering state: IdleState`, with no POST.
  **Management is never told the test was aborted; there is simply no row.**
- **Incomplete tests are represented as: nothing.** No partial trial, no abort flag, no fault
  record. The only trace is `cyclic_tests.current_cycle` left non-zero — which, per §6.5, cannot
  be distinguished from a completed run.
- **There is no Fault state and nothing to clear.** `force_stop` is reset only when a new
  `start` arrives in Idle.
- Two error paths set **`force_Stop`** (capital S) — `idle.py:33`, `start_vfd.py:22`. Python
  creates a new attribute; the intended abort **never happens**. CONFIRMED typo.

### 9.5 Power loss, reboot, and what survives

| Question | Answer |
|---|---|
| firmware loses power mid-test | valves hold their last electrical state; the VFD stops with the rig. No state is written to disk |
| what survives reboot | **only** the retained MQTT topic `ifet/firmware/{device_id}/owned-sensors` (`sensor_ownership.py`, QoS 1, retained) |
| is current test state persisted | **no.** Not the stage, not the setpoint, not the cycle index, not the elapsed hold |
| can a test resume | **no.** `fetch_on_boot` recovers *gauge ownership* only, and `IdleState.on_enter` immediately **releases** it. `cyclic_resume` is dead code (§6.2). `current_cycle` survives in Management but firmware has no path to re-enter mid-stage |
| deflection acquisition after reboot | gauges must be re-assigned by a new `start` |

**Live fault, worth stating plainly:** both SICK masters (10.1.10.229, 10.1.10.85) have been
unreachable since **2026-08-29 23:08** — "No route to host", **45 861** consecutive failures on
gateway-1 with no success in the retained log, and ICMP fails from `management`. When
`fetch_device_data` returns `None`, nothing is published, so `deflection_sensors_values` stays
empty and any test run since then posts `deflections: []`. **Deflection is currently
unmeasurable fleet-wide.**

### 9.6 Duplicate execution and command identity

| Question | Answer |
|---|---|
| can the same command execute twice | **Yes.** Two `start` messages while Idle: the first transitions out of Idle, the second is dropped by the `isinstance` guard. But two `start`s **after** a test completes will run the stage twice, and `GET /next-cyclic-test` will return the *same* stage (never marked `finished`) — so **re-running the same stage is the default behaviour, not an error** |
| is there command/request identity | **No.** No message id, no correlation id, no attempt id, no nonce, on any topic or endpoint |
| deduplication / idempotency | **None.** `POST /trials` is unconditionally create-only: `trial_number = len(trials) + 1`. A retried POST silently creates trial 2 |
| is the POST retried | **No.** Static: unguarded call — an exception propagates out of `RecoveryState.on_exit`. Cyclic: wrapped in `try/except`, logged, **and the result is lost** |
| can a trial be added to a finished test | **Yes.** The trials POST does not check `finished` (only the stage-parameter `PUT` does) |

`notify()` is published only on a successful API call, so the UI does not refresh on failure —
the one deliberate consistency measure in the path.

---

## 10. Manual / Operator Overrides

The critical distinction — **required plan vs actual execution** — is not merely blurred in
LabOS. **The actual execution is almost entirely unrecorded**, so the two cannot be compared at
all.

| Operator action | How | Changes the required plan? | Changes actual execution? | Where is the difference recorded? |
|---|---|---|---|---|
| **Drive the VFD by hand** (static) | browser slider → MQTT `vfd/command` `set_frequency` (websockets :8084, direct to broker) | no | **yes — it *is* the static pressure loop** | **nowhere.** Neither the frequency, nor the achieved pressure, nor the time to reach it |
| Choose control sensor | `sensor_id` in `start` | no | yes — which sensor gates the setpoint | **nowhere** |
| Choose deflection gauges | `selectedSensors` in `start` | no | yes — which gauges are recorded, or none | implicitly, by which `deflections` rows exist |
| Choose test type / mode | `mode` in `start` | no | yes | **nowhere** |
| Abort | MQTT `emergency_stop` | no | yes — terminates the test | **nowhere** (§9.4: no row at all) |
| Re-run a stage | publish `start` again | no | yes — a second physical run | a second `trial_number`, with no marker of why |
| **Add a stage** | `POST …/static_tests/` or `…/cyclic-tests/` | **yes** — new row, `preset = false` | yes | `preset = false`; static also `pressure_factor = ''` |
| **Override pressure / duration / cycles / direction** | `PUT …/static-tests/{i}/` or `…/cyclic-tests/{i}/` | **yes — it overwrites the derived row in place** | yes | **nowhere. The original derived value is destroyed.** Refused only once `finished = true` |
| Skip a stage | `PUT …/{i}/finish` without running it | yes — marks it done | n/a | **nowhere** — `finished` with no trial is indistinguishable from finished-with-a-trial elsewhere |
| Mark a stage finished | `PUT …/{i}/finish` | yes | no | `finished = true` |
| Reset a cyclic stage | `PUT …/{i}/reset` | yes — `current_cycle = 0`, `resume = false` | no | **nowhere** — progress is erased |
| Attach note / photo | `PUT /test-results/{id}` | no | no | `note`, `image_path` |
| Zero a gauge | implicit, at `sick/assign` | no | yes — sets the deflection datum | **nowhere** — offset is discarded on release |
| Manually control a valve | not exposed on any audited path | — | — | — |

**Two structural problems for the integration:**

1. **`PUT …/static-tests/{i}/` and `…/cyclic-tests/{i}/` mutate the derived stage in place.**
   There is no "required" column and no "as-executed" column — one row holds both. Once an
   operator edits it, `Required Pressure = 60` and `Actual Executed Pressure = 55` have already
   collapsed into a single number, and the original is gone. Any Airtable field named
   "Required Value" that we populate from `static_tests.pressure` is reporting **whatever the
   value is now**, which may not be what was required or what was run.

2. **The static VFD path means the achieved pressure is a human's doing and is never
   recorded.** `HoldingTimeState` only guarantees `|sensor| > |setpoint|` was true for **one
   sample** before the hold began. It does not guarantee the pressure was held, and nothing
   records what it actually was. For cyclic the ramp exits at ≈85% of target by design
   (`error ≥ −0.15 × setpoint`), so **the achieved pressure is systematically below the
   requirement and nobody knows by how much.**

---

## 11. Units and Conversion Boundaries

### 11.1 Pressure — PSF above the sensor, CONFIRMED both rigs

```
physical sensor  ──Modbus RTU FC3, register 22, IEEE-754 float──►  PSI
      ↓ NewSensor.read():  value × config.scale   (scale = 144)
serial_service   ──MQTT {device}/sensors/{addr}, bare float, round(...,3)──►  PSF
      ↓ state_machine: sensors_values[addr] = float(payload)     (no conversion)
comparison against setpoint from Management                       PSF vs PSF  ✅
```

`serial_service` config on **both** rigs sets `scale: 144, unit: "PSF"` on every `pressure2`
sensor. Live log lines confirm it — `sensor [2] value -0.31051501259207726 PSF` on `system-1`,
`sensor [sensor4] value -1.0024148002266884 PSF` on `system-2` — and the 2026-08-26 test shows
the control sensor climbing 0.278 → 56.044 against a 75 PSF target. **Consistent, CONFIRMED.**

> **Correction to my own first reading.** `system-1`'s *state_machine* config
> (`config1-site-b.json`) has no `scale`/`unit`, which looks like a missing PSF conversion. It is
> not: only `serial_service` reads those keys, and `serial_service` is on `config1.json`, which
> has them. The two-config split (§3.3) is a real problem, but **PSI/PSF is not one of its
> symptoms.**

The legacy `Sensor` class (`type: "pressure"`) hardcodes `× 144` at register 1028. Neither
production rig uses it — both use `pressure2`/`NewSensor`.

### 11.2 Duration — seconds everywhere, CONFIRMED

| Value | Wire/storage | Firmware internal | Proof |
|---|---|---|---|
| `static_tests.duration` | int, s | `holdtime × 10` iterations × `sleep(0.1)` | `holding_time.py:37`; production 471 rows at `30` matching the hardcoded `30` |
| `recovery_time` | int, s (config) | `× 10` × `sleep(0.1)` | `recovery.py:17` |
| `infiltration_tests.duration` | float, **s** | not used by firmware | range 321.30–1691.60 (§6.3) |
| per-cycle time | not a field | hardcoded `2 × sleep(1.0)` | measured 2.021 s/cycle |

### 11.3 Direction and sign — the sign is inert

Two code paths compute the setpoint sign in **opposite** directions:

```python
# static  (state_machine.py:368-369)
direction = data['type'] == 'outward'
self.setpoint = data['pressure'] * (1 if direction else -1)          # outward → +

# cyclic  (state_machine.py:392-394)
direction = data['type'] == 'outward'
self.positive_setpoint = data['high_pressure'] * (-1 if direction else 1)   # outward → −
self.negative_setpoint = data['low_pressure']  * (-1 if direction else 1)
self.action = 'positive' if direction else 'negative'               # same in both
```

Production confirms the cyclic sign: `type: 'outward'`, `high_pressure: 75.0`, and the log prints
`-75.0,-22.5`.

**This inconsistency has no physical effect**, because every consumer takes the magnitude:

- static: `if abs(sensors_values[sensor_id]) > abs(self.setpoint)`
- cyclic: `self.setpoint = max(abs(positive_setpoint), abs(negative_setpoint))`

**Direction is carried solely by `action`, and both paths agree: `type == 'outward'` ⇒
`action = 'positive'` ⇒ the valves whose `role` contains `POSITIVE`.** That is the real direction
contract. The sign arithmetic is dead weight — harmless today, a trap for anyone who later
introduces a signed comparison.

Note the consequence for the sensor sign: pressure readings are signed (`−0.31`, `+0.13` at rest),
and the setpoint comparison is on magnitude. **An inward test would satisfy `|sensor| > |setpoint|`
on an outward overpressure of the same magnitude.** No layer checks that the sign of the reading
matches the requested direction.

### 11.4 Deflection — the one broken boundary

```
SICK linear gauge  ──IO-Link──►  master  ──HTTP GET .../processdata/getdata/value──►  byte array
      ↓ gateway: value = (raw[0] << 8) + raw[1]        unsigned 16-bit, big-endian
      ↓ comment says "# Store the raw value (in mm)"   ← ASSERTION, no device scale applied
      ↓ adjusted = value − zero_offset                 offset captured at sick/assign
      ↓ convert_units():  × MM_TO_INCH (0.0393701)     UNIT_OF_MEASUREMENT=inch
      ↓ "{:.2f}".format(...)                            2 decimal places
MQTT sick/sensors/{gauge}  ──►  firmware stores JSON verbatim, NO arithmetic
      ↓ POST /trials
deflections.max_deflection  Float   ← labelled inches, is actually counts × 0.0393701
```

**Firmware applies no scale, no offset, no calibration and no unit conversion to deflection.**
The conversion boundary is entirely inside the SICK gateway on `management`. Full analysis in §12.

### 11.5 Unit inventory — code/runtime evidence only

| Quantity | Wire / storage unit | Internal firmware unit | Conversion | Physical unit | Evidence |
|---|---|---|---|---|---|
| design pressure | **PSF**, Float NOT NULL | not received | — | PSF | `models.py`; derivation matches DB exactly |
| static target pressure | **PSF**, Float | PSF (signed, sign inert) | none in firmware | PSF | §11.1, §11.3 |
| cyclic high/low pressure | **PSF**, Float | PSF, then `max(abs)` | none in firmware | PSF | production log |
| measured pressure | **PSF** on MQTT, 3 dp | PSF | `× 144` from PSI in `serial_service` | PSF | live logs, both rigs |
| sensor native reading | IEEE-754 float | — | Modbus FC3 reg 22 | **PSI** | `new_sensor.py:35` |
| hold duration | **seconds**, Integer | seconds | none | s | `holding_time.py:37` |
| recovery_time | **seconds**, config int | seconds | none | s | `recovery.py:17` |
| infiltration duration | **seconds**, Float | not used | — | s | value range (§6.3) |
| cycles | **count**, Integer | count | none | — | derivation matches |
| VFD frequency | **Hz**, float | Hz | Modbus FC6 reg 8193, 2 decimals | Hz | `vfd_node.py` |
| deflection | **"inch"** (mislabelled) | pass-through | `counts × 0.0393701` | **UNKNOWN** | §12 |
| `recovery` (result field) | Float, **seconds** | config constant | none | **s, in a column of inches** | §12.4 |
| leakage | Float, unit undeclared | **not produced** | — | **UNKNOWN** (`cfm/ft²`? never stated) | `models.py` |
| missile weight | Float, undeclared | not produced | — | **UNKNOWN** (kg? lb?) | `models.py` |
| shot velocity | Float, undeclared | not produced | — | **UNKNOWN** (m/s? ft/s?) | `models.py` |
| shot area | Float, undeclared | not produced | — | **UNKNOWN** (m²? ft²?) | `models.py` |

**Units claimed in documentation but NOT supported by code or runtime**, and therefore excluded:
`mm` for deflection (the gateway's `mm` is an unverified assertion about raw counts, not a
measurement); `minutes` for infiltration duration (contradicted, §6.3); `cfm/ft²` for leakage,
`m/s` for velocity, `kg` for missile weight, `m²` for area (**no unit is declared anywhere** for
any of these four — they are unknown, not confirmed).

### 11.6 Documentation vs code vs runtime — discrepancies, not reconciled

| Claim | Documentation | Code | Production runtime | Verdict |
|---|---|---|---|---|
| VFD Modbus address | `CLAUDE.md`: "**12**, not 5, on the production rigs" | from config | **`system-1` = 12, `system-2` = 5.** `system-2`'s VFD answers fine at 5; `system-1`'s answered fine at 12 on 2026-08-26 | **Doc is wrong as a fleet-wide rule.** It is per-rig. Do not "fix" `system-2` to 12 |
| system-1 serial device | `CLAUDE.md`: "`/dev/ttyUSB0`, not `/dev/ttyACM0`" | `config1.json` says ttyUSB0; `config1-site-b.json` says ttyACM0 | container maps **ttyUSB0**; sensors read fine | **Doc correct**, for the config that matters |
| system-1 config | `CLAUDE.md`: "bind-mounts `config1.json`" | — | true for `serial_service` only; `state_machine` + `valves` are on `config1-site-b.json` | **Doc incomplete** (§3.3) |
| `active` flag gates polling | `CLAUDE.md`: it does not | `add_sensor` ignores `active` | system-1's `active:false` Flow sensor **is** polled | **Doc correct**, re-confirmed |
| infiltration duration | old annotation: minutes | no firmware use | 321–1692, full floats | **Doc wrong — seconds** |
| cyclic direction pattern | our note: "alternating inward/outward" | `i < 4` | 0–3 inward, 4–7 outward | **Our note wrong** for cyclic; right for static |
| deflection in inches | schema/API imply inches | gateway asserts raw counts are mm | ±1288.86 | **All three disagree** (§12) |
| pass/fail computed | write contract assumes a verdict exists | no writer | all real trials NULL | **Contract assumes something production cannot supply** |

---

## 12. Deflection Data Investigation — PRIORITY

### 12.1 The pipeline, stage by stage

| Stage | Raw type | Raw unit | Conversion | Sign | Calibration source | Owner |
|---|---|---|---|---|---|---|
| physical gauge | SICK IO-Link linear position sensor | device-native | — | device | factory | hardware |
| IO-Link master (10.1.10.229 / .85) | JSON `{"iolink":{"value":[bytes…],"valid":bool}}` | **device process-data units — never read** | — | — | — | hardware |
| gateway decode | `value = (raw[0] << 8) + raw[1]` | **unsigned 16-bit, 0…65535** | **none — no device scale factor** | **unsigned: negatives are unrepresentable** | — | **gateway** |
| gateway assertion | `raw_value_numeric = value  # "(in mm)"` | **asserted mm by comment only** | — | — | — | **gateway** |
| zero offset | `offset = devices[id]["raw_value"]` at `sick/assign` | raw counts | `adjusted = value − offset` | difference may be negative → **this is the only source of negative values** | **captured at assign; deleted at release** | gateway |
| max tracking | `if abs(adjusted) > abs(current_max)` | raw counts | — | magnitude-max, sign preserved | reset to `None` at assign | gateway |
| permanent tracking | `latest_values[id] = adjusted` every poll | raw counts | — | signed | reset at assign | gateway |
| unit conversion | `round(value × 0.0393701, 4)` | **counts → pseudo-inches** | `MM_TO_INCH` | preserved | `UNIT_OF_MEASUREMENT=inch` (env) | gateway |
| MQTT publish | `"{:.2f}".format(...)` — **a string** | pseudo-inches, 2 dp | — | preserved | — | gateway |
| **firmware** | stores the dict verbatim | **no arithmetic at all** | **none** | — | **none** | **firmware: pass-through** |
| HTTP POST | `max_value` → `max_deflection`, `permanent_value` → `permanent_deflection` | pseudo-inches | none | preserved | — | firmware |
| Pydantic | `float` | none | none | — | none | report-api |
| persistence | `Float NOT NULL` | **labelled inches** | none | preserved | — | postgres |
| reporting | read verbatim | inches | none | — | — | report-api |

### 12.2 The gateway's published payload

```json
{"valid": true, "raw_value": <converted>, "value": "<2dp>",
 "permanent_value": "<2dp>", "offset": <converted>, "zeroed": bool,
 "assigned_to": "<device_id>|free", "max_value": "<2dp>",
 "units": "inch", "timestamp": <epoch>}
```

The gateway **does** publish a `units` field. **Firmware ignores it**, and there is no unit
column anywhere downstream. `max_value` and `permanent_value` are **strings**, coerced to float
by Pydantic.

### 12.3 Why the historical values are not inches — the arithmetic

Production: `max_deflection` ∈ [−1280.91, 1288.86], `permanent_deflection` ∈ [−1274.17, 1284.13].

Dividing by the gateway's own constant `MM_TO_INCH = 0.0393701` recovers the raw word:

| `max_deflection` | implied raw count | residual from integer |
|---|---|---|
| 1288.86 | 32737.03 | 0.026 |
| 1287.87 | 32711.88 | 0.120 |
| 1287.44 | 32700.96 | 0.042 |
| 1286.85 | 32685.97 | 0.028 |
| 1285.79 | 32659.05 | 0.048 |

Two things fall out, and together they are conclusive:

1. **The extremes sit at the signed-int16 full-scale boundary.** The largest implied count is
   **32737**, against `2^15 − 1 = 32767`. Values cluster just below it. A physical
   displacement measurement would have no reason to pile up there; a **16-bit word being read
   with the wrong signedness or without its scale factor** has exactly that reason.

2. **The residuals are fully explained by the gateway's own formatting, so the underlying
   counts are integers.** The gateway emits `"{:.2f}"`, so the stored value is rounded to 2
   decimals — ±0.005 in, which is ±0.005/0.0393701 = **±0.127 counts**. Every observed residual
   (0.026–0.120) is inside that band. The decimal-place histogram agrees: 945 rows at 2 dp,
   86 at 1, 51 at 0 — i.e. 2-dp strings with trailing zeros dropped by the float column.

**Conclusion:** `deflections.max_deflection` holds **`round(raw_uint16_difference × 0.0393701, 2)`**.
It is a raw IO-Link count scaled by a millimetre-to-inch constant. It is **not inches**, and it
is not millimetres either — nothing established that a count equals a millimetre. That
equivalence is asserted by a code comment and by nothing else.

Supporting separation: **all 20 implausible rows (|value| > 20 in) are in the SICK-named set;
zero are in the seed set** (§12.5). And **47 of the 609 SICK rows are `max = permanent = 0`** —
consistent with a gauge that was assigned but never returned data, which is also the current
fleet state (§9.5).

### 12.4 `recovery` — CONFIRMED, and it is not a measurement

| Provenance | rows | distinct `recovery` values |
|---|---|---|
| SICK-named (**real firmware**) | 609 | **1** — every row is `60` |
| `Gauge N` (**seed data**) | 473 | **390** |

`60` is exactly `recovery_time` from the live config on both rigs. Firmware passes it straight
into the payload:

```python
# recovery.py:36-41 — static
self.machine.api.finish_static_test(project_id, index, deflections, self.recovery_time)
# state_machine.py:529-534 — cyclic, skip-recovery path (both rigs)
self.api.finish_cyclic_test(project_id, index, deflections, 0)
```

**`recovery` in the real data is the configured post-test hold, in seconds, duplicated onto every
deflection row.** It says nothing about how the specimen recovered. Cyclic tests post `0`.

Meanwhile the seed data computed `recovery = max_def − perm_def` (`populate_db.py:159`) — a
*displacement* in inches.

**So one NOT NULL Float column carries two incompatible quantities: seconds in every real row,
inches in every seeded row.** This resolves the `recovery` limb of contract §10.27 completely,
and it means the column cannot be exported under any single unit.

### 12.5 Gauge naming — CONFIRMED, and it is provenance, not rig generation

Both schemes and their statistics:

| | `1-1`…`2-8` | `Gauge 1`…`Gauge 4` |
|---|---|---|
| rows | **609** | **473** |
| `test_id` range | **284 – 619** | **3 – 274** (disjoint) |
| distinct `recovery` | 1 (=60) | 390 |
| `max_deflection` range | −1280.91 … 1288.86 | 0.37 … 14.73 |
| rows with \|value\| > 20 | 20 | **0** |
| rows with max = perm = 0 | 47 | **0** |
| parent trial's `result` | **always NULL** | **always set** (109 true / 51 false) |

**Origin of `1-1`…`2-8`: CONFIRMED — the SICK gateway configs on `management`.**
`sick_gateway-1` `config.json` declares device ids `1-1`…`1-8`; `sick_gateway-2` declares
`2-1`…`2-8`. Firmware relays whatever gauge name the operator selected, which is a gateway id.

**Origin of `Gauge 1`…`Gauge 4`: CONFIRMED — `report-api` `app/utils/populate_db.py`:**

```python
gauge_names = ["Gauge 1", "Gauge 2", "Gauge 3", "Gauge 4"]     # line 155
max_def  = random.uniform(0.5, 15.0)                            # line 157
perm_def = random.uniform(0.1, max_def * 0.3)                   # line 158
recovery = max_def - perm_def                                   # line 159
result   = random.choice([True, True, False])                   # line 145
current_cycle = random.randint(0, c) if random.random() > 0.7 else c   # line 132
```

Every observed property matches: the 0.37–14.73 range against `uniform(0.5, 15.0)` (0.37 arising
from `perm_def` rounding), the 390 distinct recovery values against a computed difference, the
109:51 result split against `choice([True, True, False])` (2:1), and the disjoint earlier
`test_id` range.

**So the "naming inconsistency" is not a firmware, config or rig-generation issue. It is the
boundary between seeded demo data and real measurements**, and the gauge name is the most
reliable discriminator we have for telling them apart.

Classification of the §11 candidates:

| Candidate origin | Verdict |
|---|---|
| Firmware | **RULED OUT** — firmware relays the operator's string; it invents no name |
| Management | **CONFIRMED for `Gauge N`** — `populate_db.py` |
| Configuration | **CONFIRMED for `1-1`…`2-8`** — SICK gateway `config.json` |
| Different rig generations | **RULED OUT** — deployed firmware is byte-identical bar `idle.py` (§3.2); both schemes appear across projects, not per device |
| Operator entry | **POSSIBLE but unnecessary** — the UI selects from gateway ids; no free-text gauge-naming path was found |
| Unknown | resolved |

### 12.6 Multiple firmware generations?

**No.** Deployed `state_machine` is byte-identical on both rigs except `states/idle.py`, and that
difference touches valve handling only — not deflection, not payload shape, not units. **There is
exactly one deflection payload format in production**, and it has been the same since the SICK
path began (trial 284).

### 12.7 Classification

| Finding | Class |
|---|---|
| Firmware performs no deflection arithmetic — pure pass-through | **CONFIRMED** |
| Gateway reads two bytes as a big-endian **unsigned** 16-bit word | **CONFIRMED** (source) |
| No device scale factor is applied; "mm" is a comment, not a measurement | **CONFIRMED** (source) |
| Stored value = `round(raw_count_difference × 0.0393701, 2)` | **CONFIRMED** (arithmetic reproduces every extreme; rounding explains every residual) |
| The only calibration is a zero offset captured at `sick/assign`, discarded at release | **CONFIRMED** |
| `max_deflection` is magnitude-max with sign preserved; `permanent_deflection` is the last sample while assigned | **CONFIRMED** |
| Historical values represent raw counts, not inches | **CONFIRMED** |
| Extremes correspond to the int16 full-scale boundary (32767) | **STRONGLY INDICATED** |
| `recovery` is `recovery_time` in seconds (real rows) / `max−perm` in inches (seed rows) | **CONFIRMED** |
| Gauge naming = two provenances (gateway config vs `populate_db.py`) | **CONFIRMED** |
| Multiple firmware generations with different formats | **RULED OUT** |
| **The correct physical scale factor** | **UNKNOWN** — needs the IO-Link device descriptor plus a known-displacement test (§17, T4) |
| Whether a signedness bug, a missing scale, or both | **UNKNOWN** — `NOT VERIFIED — would require a live gauge reading` |
| `permanent_deflection` as a *physically valid* permanent set | **UNKNOWN** — it is the last sample before release, so its validity depends entirely on `recovery_time`; cyclic (skip-recovery) takes it with **no** recovery period |

---

## 13. Intended vs Actual Architecture

| Concern | Intended / current docs | Source code | Production runtime | Conclusion |
|---|---|---|---|---|
| **programme derivation** | unstated; write contract implies requirements drive the rig | `report-api` `domain/*_pressure_calculator.py` + project creation | project 78 matches the factor arrays exactly, and the boundary log shows firmware *pulling* the derived stage | **Model B via callback pull. 100% Management-owned.** Firmware does no derivation |
| **pressure units** | PSF | `scale: 144` PSI→PSF in `serial_service` only | both rigs log PSF; setpoint comparison is PSF vs PSF | **PSF, consistent. CONFIRMED** |
| **duration units** | "minutes" (old annotation) for infiltration | `× 10` × `sleep(0.1)` ⇒ seconds | static 30 s; infiltration 321–1692 | **Seconds. Documentation wrong** |
| **result calculation** | contract assumes a Pass/Fail exists | **no writer** for `TestResult.result` | 129/129 real trials NULL; the 275 populated are seed | **Nobody owns pass/fail. The contract assumes a value production cannot produce** |
| **attempt identity** | contract has `LabOS Attempt ID`, upsert, immutability | none — no id, no nonce, `trial_number = len+1` | duplicate POST would create trial 2 | **No identity or idempotency exists below the new P1 schema.** The append-only attempt model is a *new* capability, not a reflection of production |
| **deflection conversion** | inches | gateway: `(b0<<8)+b1` × 0.0393701, no device scale | ±1288.86 = counts × 0.0393701 | **Broken in the gateway. Firmware is not at fault.** Do not export |
| **gauge naming** | inconsistent, cause unknown | gateway `config.json` vs `populate_db.py` | disjoint `test_id` ranges, disjoint statistics | **Two provenances: real vs seed. RESOLVED** |
| **manual stages** | "operator-authored stages also exist" | `preset` flag; `pressure_factor=''` for ad-hoc static | static 10/501, cyclic 2/626 | **Confirmed, and rare. Firmware never reads `preset` — indistinguishable at the boundary** |
| **abort** | implied to be reportable | `force_stop` skips the POST entirely | `system-2` 2026-08-17: abort, no row | **An aborted test is invisible to Management. No abort or fault channel exists** |
| **firmware→Mgmt result payload** | implied rich | **one field**: `deflections[]` | `{"deflections": [], "id": 637, "trial_number": 1}` | **Four values per gauge, and one of them is a config constant** |
| **cyclic per-cycle pressure control** | implied closed-loop | every check commented out, `if True: sleep(1.0)` | 2.021 s/cycle measured | **Open loop. `low_pressure` is inert** |
| **static pressure control** | implied automatic | no VFD command in `HoldingTimeState`; dead `self.freq` | operator slider publishes `vfd/command` | **Manual. The operator is the control loop** |
| **resume** | `current_cycle` + `resume` columns exist | `cyclic_resume` only ever `False`; setter commented out | `current_cycle = 49` stranded on project 78 | **Resume is dead code. The DB seam exists; firmware cannot use it** |
| **turbo** | system-2 runs turbo for valves 5/6 | requires `devices.turbo_charger` non-null | both devices `turbo_charger = NULL` | **All state-machine turbo paths dead in production.** How valves 5/6 are driven: UNKNOWN, out of scope |
| **VFD Modbus address** | `CLAUDE.md`: "12, not 5" fleet-wide | per-rig config | sys-1 = 12 (worked 08-26), sys-2 = 5 (working now) | **Per-rig, not fleet-wide. Documentation over-generalises** |

---

## 14. Implications for Airtable Integration

### 14.1 Requirements In — what Airtable actually needs to provide

Because Management derives everything from the design-pressure pair, **the requirement surface is
tiny.** Do not model derived values; they would be redundant at best and a second source of truth
at worst.

| Airtable field | → Management field | → Management derivation | → Firmware input | Needed? |
|---|---|---|---|---|
| Inward design pressure (**PSF**) | `projects.inward_design_pressure` Float NOT NULL | static even-index pressure; cyclic stages 0–3; **water stage = ×0.15** | `pressure` / `high_pressure` / `low_pressure` | **YES — essential** |
| Outward design pressure (**PSF**) | `projects.outward_design_pressure` Float NOT NULL | static odd-index; cyclic stages 4–7 | same | **YES — essential.** 36/78 projects (46%) differ from inward: **must be two fields** |
| Water infiltration required? (bool) | **`has_water_infiltration`** — creation input, **not stored** | inserts the 900 s / 0.15×IDP static stage at index 4 and shifts stages 4–5 → 5–6 | `pressure`, `duration = 900` | **YES** — changes the programme; unrecoverable afterwards |
| Specimen / project name | `projects.name` | — | — | YES (identity; unique per parent) |
| Project / parent | `projects.parent_id` → `project_parents` | — | — | YES (identity) |
| Which rig | `projects.device_id` (1 or 2) | — | — | YES (routing) |
| **Deflection limit / acceptance criterion** | **no column exists** | **no derivation exists** | — | **YES, if Airtable expects Pass/Fail** — see §8. This is a **new LabOS field and a new build** |
| Missile class, weight; shot count | `missile_impact_tests.*`, `shots.*` | none | **none — manual** | Only if impact is in scope; units UNKNOWN (§16 Q4) |
| Air infiltration target pressure/duration | `infiltration_tests.*` | none | **none — manual** | Only as a manual record; not executable |
| — | — | — | — | |
| ~~stage pressures, hold times, cycle counts, high/low pressures, stage directions, stage order~~ | ~~`static_tests`, `cyclic_tests`~~ | **already derived by Management** | — | **NO — do not cross the boundary.** Sending these creates a second source of truth for values LabOS computes deterministically |

**This strengthens contract §10.19 rather than relieving it.** Because a single design-pressure
number fans out into 14 stages, an extraction-shifted value (60 → 9) does not corrupt one field —
it corrupts **the entire programme**, and §5.3 shows there is no validation at any layer that
could catch it. The standing rule (no rig is driven from Airtable requirement values until the
extractor is fixed) is the correct one, and this audit gives it a sharper argument: **the blast
radius of one wrong number is the whole test.**

### 14.2 Results Out — what LabOS actually produces

| Value | Class | Available today? |
|---|---|---|
| `max_deflection` per gauge | **raw firmware measurement** (gateway-produced, firmware-relayed) | yes — **unit unverified, do not export** (§14.3) |
| `permanent_deflection` per gauge | **raw firmware measurement** | yes — same caveat, plus a definitional problem (§12.7) |
| `deflection_gauge` | integration metadata | yes — but the value also encodes provenance (§12.5) |
| `recovery` | **firmware configuration**, mislabelled as a measurement | yes — **seconds in real rows, inches in seed rows. Do not export** |
| `trial_number` | **management-derived** | yes |
| `note`, `image_path` | **operator metadata** | yes |
| `current_cycle` | raw firmware measurement (progress) | yes — but maxes at `cycles − 1` and cannot signal completion (§6.5) |
| `finished` | **operator metadata** (an operator action, not a machine outcome) | yes |
| **Pass/Fail** | — | **NO — produced by nothing** (§8) |
| **achieved / max pressure** | — | **NO — never measured or stored** |
| **cycles completed** | — | **NO — not distinguishable from cycles attempted** |
| **test start / end timestamps** | — | **NO — no datetime column on `test_results`** |
| **actual duration** | — | **NO** |
| **leakage (water)** | — | **NO from firmware**; `infiltration_tests.leakage` is manual and probably seeded (§6.3) |
| **abort / fault information** | — | **NO — an aborted test produces no row at all** |
| Shot results | **operator metadata** | yes — the only real pass/fail in LabOS |

**The honest summary for the call: LabOS can currently export three deflection numbers per gauge
(one of which is a config constant), a trial number, and operator notes. It cannot export a
verdict, a pressure, a duration, a completion state or a timestamp.**

### 14.3 Safety — data that must NOT be exported until its semantics are verified

| Field | Why | Gate |
|---|---|---|
| **`max_deflection`, `permanent_deflection`** | not inches; raw counts × 0.0393701; extremes at the int16 boundary; scale factor unknown | T4 (§17) — controlled gauge test, then a gateway fix and a decision on historical rows |
| **`recovery`** | seconds in real rows, inches in seed rows, in one column. Never a specimen recovery measurement | Rename/split in LabOS, or exclude permanently |
| **All `infiltration_tests` rows** | full-mantissa random floats, no firmware write path — STRONGLY INDICATED seed data | Confirm with the lab whether any row is real |
| **Every row whose `deflection_gauge` matches `Gauge %`** | CONFIRMED synthetic (`populate_db.py`) | Exclude by predicate; 473 of 1082 rows |
| **Every `test_results.result` value** | CONFIRMED synthetic — no writer exists | Exclude; do not present as a verdict |
| **`current_cycle` as "cycles completed"** | off by one and never reset on completion | Exclude, or fix the off-by-one first |
| `shots.velocity`, `.area`, `missile_impact_tests.missile_weight` | **no unit declared anywhere** | Establish units with the lab (§16 Q4) |
| Any value from a test run since **2026-08-29 23:08** | gauges offline; deflections are `[]` or absent | Restore the SICK masters |

**A concrete export predicate is available and cheap:** real firmware-produced deflection rows
are exactly those where `deflection_gauge ~ '^[12]-[1-8]$'`. Everything else is seed data. Use it
in the sync worker (P4) regardless of how the unit question resolves.

---

## 15. Confirmed Contract Decisions

These can be frozen now; production evidence is unambiguous.

1. **Airtable supplies requirements, never execution stages.** The integration carries the
   design-pressure pair (+ the water-infiltration boolean and identity fields). Management
   derives all 14 stages. **Do not add stage-level requirement fields to the read side.**
2. **Two independent design pressures, both PSF, both mandatory.** 46% of production projects
   have asymmetric values; the derivation reads inward for static even indices / cyclic 0–3 and
   outward for static odd / cyclic 4–7. A single "design pressure" field would silently corrupt
   half the fleet's programmes.
3. **Pressure is PSF at every boundary above the sensor.** Confirmed on both rigs. No PSI ever
   crosses the Management↔Firmware boundary.
4. **All durations are seconds.** Static hold 30 s (preset), water 900 s, recovery 60 s,
   infiltration 321–1692 s. The "minutes" annotation is retired.
5. **Direction is a two-valued enum `inward` | `outward`**, mapping to valve roles
   `NEGATIVE` | `POSITIVE`. Pressure values crossing the boundary are **unsigned magnitudes**;
   the sign arithmetic in firmware is inert. Airtable's `+60/60` must resolve to
   *(outward 60 PSF, inward 60 PSF)* — two quantities, not a signed one.
6. **Cyclic stage direction is 0–3 inward, 4–7 outward** — not alternating. Static *is*
   alternating, starting inward.
7. **The firmware→Management result payload is `deflections[]` and nothing else.** Any Airtable
   result field beyond deflection, trial number and operator notes requires a LabOS-side build.
8. **Pass/Fail has no owner in production.** It must be either newly computed by Management from
   a newly supplied acceptance criterion, or explicitly carried as an operator judgement.
9. **`recovery` is not a specimen measurement** and must not be mapped to any Airtable
   recovery/deflection field.
10. **Deflection values are quarantined** pending T4.
11. **Water infiltration executes as a static test** (900 s at 0.15 × inward DP), not as an
    infiltration test. `infiltration_tests` and `missile_impact_tests` are manual records with no
    firmware path.
12. **`has_water_infiltration` must cross the boundary** — it changes the stage list and is not
    recoverable from stored state.
13. **No idempotency exists below the P1 schema.** The append-only attempt model with
    `LabOS Attempt ID` is a *new* capability. Nothing in production dedupes, and
    `POST /trials` is unconditionally create-only.
14. **Real vs seed data is separable** by `deflection_gauge ~ '^[12]-[1-8]$'`. Apply it in P4.

---

## 16. Open Questions / Unsafe Assumptions

| # | Question | Why it matters | Owner |
|---|---|---|---|
| Q1 | **Where does Pass/Fail come from?** Management computes it from a supplied deflection limit (new field + new build), or it stays an operator judgement? | The write contract has the field; production has no source. Blocks the results side | **IFET + us — decide on the call** |
| Q2 | **What is the correct IO-Link scale factor**, and is the gateway decode signed or unsigned? | Determines whether 1082 historical deflection rows are salvageable or must be discarded | us (needs T4) |
| Q3 | **Are the historical SICK deflection values worth back-correcting**, or is the record written off from the SICK-era start (trial 284)? | Decides whether Airtable ever receives pre-fix deflection | IFET |
| Q4 | **What are the units of `shots.velocity`, `shots.area`, `missile_impact_tests.missile_weight`, `infiltration_tests.leakage`?** None is declared anywhere | Four fields cannot be exported without this | IFET (lab) |
| Q5 | **Is any `infiltration_tests` row real?** All 37 look generated | Decides whether air/water infiltration results exist at all | IFET |
| Q6 | **Should `permanent_deflection` be measured after a defined recovery period?** Today it is the last sample before release, and cyclic takes it with no recovery at all | It is not currently a permanent set in the ASTM sense | IFET + us |
| Q7 | **Should completion be machine-reported?** Firmware never sets `finished`, and `current_cycle` cannot distinguish completed from aborted | Airtable needs to know a test finished | us (LabOS build) |
| Q8 | **Should an abort produce a record?** Today it produces nothing | Silent data loss; also a retest-model question | us |
| Q9 | **Should the achieved pressure be recorded?** Cyclic ramps to ≈85% of target by design; static is operator-driven | "Required 60, achieved 55" is currently unrepresentable | IFET + us |
| Q10 | Is `system-1`'s `state_machine`/`valves` on `config1-site-b.json` intentional? | Valve roles and GPIO pins for a production rig come from a config named for another site | IFET / deployment owner |
| Q11 | Why has `system-2` not received the `idle.py` RELIEF fix, and its daily cron restart runs the pre-fix path? | A known valve bug is live on a production rig | deployment owner |
| Q12 | When will the SICK masters be restored? | No deflection can be measured until then | IFET |

**Unsafe assumptions to retire:**

- ~~"Firmware may derive some stages."~~ It derives none.
- ~~"Cyclic presets alternate inward/outward."~~ 0–3 inward, 4–7 outward.
- ~~"Cyclic execution tracks high/low pressure per cycle."~~ Open loop, 2.0 s/cycle, `low_pressure` inert.
- ~~"Static pressure is controlled automatically."~~ The operator is the loop.
- ~~"`recovery` is a measurement."~~ Config constant.
- ~~"Deflection is in inches."~~ Raw counts × 0.0393701.
- ~~"Gauge naming differs by rig generation."~~ It differs by real-vs-seed provenance.
- ~~"VFD address is 12 fleet-wide."~~ Per-rig: sys-1 = 12, sys-2 = 5, both correct.
- ~~"An aborted or failed test is recorded somehow."~~ It produces no row.

---

## 17. Recommended Controlled Non-Production Tests

Every claim marked `NOT VERIFIED — would require active test / state change` maps to one of
these. **All of them need the `test` node back** (offline since ~2026-07-24) — which makes
recovering it the highest-leverage infrastructure ask in this report.

| # | Test | Establishes | Blocked on | Risk if skipped |
|---|---|---|---|---|
| **T1** | Full static stage on `test` with instrumented capture: log the MQTT `start`, the GET response, the `{device_id}/status` stream, and the POST body/response | The static contract end-to-end; whether the hold is actually held; the real state timing | `test` node | The static path is **source-only verified** — the last production static run (2026-08-17) was aborted |
| **T2** | Cyclic stage with a small `cycles` (e.g. 6) on `test` | Confirms 2.0 s/cycle at another cycle count; the `update_status` off-by-one; whether `low_pressure` truly has no effect | `test` node | Open-loop finding rests on one production run |
| **T3** | Abort mid-test (`emergency_stop`) and broker-disconnect on `test` | Whether valves/VFD are left energised on disconnect (§9.3); that an abort really posts nothing | `test` node | **Safety-relevant and currently only STRONGLY INDICATED** |
| **T4** | **Deflection calibration — the priority.** One SICK gauge on a bench: read raw `processdata` bytes, displace by known increments (e.g. 10.00 mm gauge block), and record the raw word, the gateway's published value, and the DB value | **The scale factor and signedness.** Answers Q2, unblocks every deflection export, and decides Q3 | SICK master restored + one gauge | Deflection stays unexportable. This is the single highest-value test in the list |
| **T5** | Duplicate `start` and duplicate `POST /trials` against a throwaway DB | Confirms two trials are created; sizes the idempotency work | isolated stack | Idempotency claims stay source-only |
| **T6** | Water stage (900 s, 0.15 × IDP) on `test` | That firmware treats it as an ordinary static hold; whether any leakage capture is possible at all | `test` node | Water infiltration contract is source-only |
| **T7** | Power-cut a rig mid-test on `test` | What survives reboot; whether retained gauge ownership recovers cleanly | `test` node | Reboot behaviour is source-only |
| **T8** | Rehearse the `config1-site-b.json` correction off-production | Whether `system-1`'s valve roles/pins are correct for its wiring | isolated compose project | §3.3 stays an open production risk |

**Nothing in this list may be run on `system-1`, `system-2` or `management`.**

---

## 18. Evidence Index

| Claim | Evidence |
|---|---|
| Fleet inventory, image dates | `docker ps` / `docker images` on both rigs; `management` `docker ps` |
| `management` branch/SHA | `git rev-parse` on the node → `latest` @ `90f9595`, clean |
| Deployed = repo except two files | md5 of every `.py` in each container vs the local clone |
| `idle.py` divergence on `system-2` | `diff -u src/state_machine/states/idle.py <deployed>` |
| `vfd_node.py` divergence on `system-1` | `diff -u src/serial_service/vfd_handler/vfd_node.py <deployed>` |
| `system-1` two-config split | `docker inspect --format '{{range .Mounts}}…'` per container + md5 of each `/app/config.json` |
| PSF scaling live | `serial_service` logs, both rigs: `... value <float> PSF`; `config1.json` / `config2.json` `scale:144, unit:PSF` |
| `recovery_time = 60`, `cyclic_skip_recovery = true`, both rigs | `python3 -c json.load` on each live `config.json` |
| VFD addresses 12 / 5 | live `serial_service` configs; 2026-08-26 log shows `vdf_feedback` tracking on sys-1 |
| **The MQTT `start` payload** | `system-1` `state_machine` log, 2026-08-26 16:48:26,184 |
| **The derived cyclic stage on the wire** | same log, 16:48:26,209 — `high 75.0 / low 22.5 / cycles 50 / index 4` |
| `GET /devices/1` response | same log, 16:48:26,197 — `turbo_charger: None` |
| **2.021 s/cycle open loop** | same log, 16:48:53.407 → 16:50:34.481, 50 cycles |
| VFD closed-loop ramp (cyclic) | same log, `freq_command` 0→35 Hz vs `vdf_feedback` |
| **The POST /trials response** | same log, 16:50:53,589 — `{"deflections": [], "id": 637, "trial_number": 1, …}` |
| Abort posts nothing | `system-2` log 2026-08-17 14:15:05 — `RecoveryState` → `Holding time interrupted` → `IdleState` |
| `system-2` daily cron restart | `system-2` log — bare `Entering state: IdleState` at 09:30 UTC daily |
| Derivation factor arrays | `report-api` `app/domain/static_test_pressure_calculator.py`, `cyclic_test_pressure_calculator.py` |
| Programme generator | `report-api` `app/main.py:124` `create_project_for_device` |
| Derivation matches production exactly | `SELECT … FROM static_tests / cyclic_tests WHERE project_id=78` vs `projects` DP 75/75 |
| Water stage = 0.15 × inward DP, 900 s | `main.py:207-217`; `SELECT … WHERE duration=900` → ratio 0.1500 across all rows |
| Route inventory | `grep "@app\.(get|post|put|patch|delete)" main.py` |
| Result payload schema | `app/data/schema.py` `StaticTestResultCreateSchema`, `DeflectionCreateSchema` |
| Data model, no pressure/time columns | `app/data/models.py` |
| **No writer for `TestResult.result`** | `grep "\.result\b\|result=\|result =" main.py` → only `result=None` ×2 + read-only uses; `PUT /test-results/{id}` takes `note`/`image` only |
| **Real trials all NULL** | `SELECT … GROUP BY` scheme × result → SICK 129 NULL / 0 set; GaugeN 109 true, 51 false, 0 NULL |
| Firmware never sets `finished` | `create_*_test_trial` bodies; project 78 stage 4 `finished=false, current_cycle=49` |
| SICK gateway decode + units | deployed `sick_mqtt_gateway.py` `process_device_data`, `convert_units`, `MM_TO_INCH` |
| `UNIT_OF_MEASUREMENT=inch`, real masters | `docker inspect` env on both gateways |
| Gauge ids `1-1…1-8`, `2-1…2-8` | both gateway `config.json` files |
| **Raw-count reconstruction** | `SELECT max_deflection, max_deflection/0.0393701 …` → 32737, 32711, 32700…; residuals ≤ 0.13 |
| 2-dp formatting explains residuals | `"{:.2f}".format` in the gateway; `SELECT length(split_part(...))` → 945/86/51 |
| **`recovery`: 1 distinct value in real rows** | `SELECT scheme, count(DISTINCT recovery)` → SICK 1 (=60), GaugeN 390 |
| **Seed data provenance** | `grep` `app/utils/populate_db.py` lines 132, 145, 155, 157-159 |
| Disjoint `test_id` ranges | `SELECT scheme, min(test_id), max(test_id)` → 3–274 vs 284–619 |
| Implausible values only in SICK rows | `count(*) FILTER (WHERE abs(max_deflection) > 20)` → SICK 20, GaugeN 0 |
| Preset vs ad-hoc counts | `SELECT preset, count(*) …` on both stage tables |
| Infiltration is seconds | `SELECT duration …` → 321.30–1691.60, full mantissas |
| Turbo disabled | `SELECT … FROM devices` → both `turbo_charger` NULL |
| Impact is manual | `models.py` `MissileImpactTest`/`Shot`; `SELECT count(*)` → 39 / 114; `shots.result` 72/42 |
| **Gauges offline since 2026-08-29 23:08** | gateway logs (45 861 failures, no success), `curl` empty, ICMP fails |
| No auth | `mosquitto.conf` → `allow_anonymous true`, no TLS; no auth on any `report-api` route |
| Browser publishes `vfd/command` | `grep -rl "vfd/command"` in the served React bundle |
| `alembic_version` | `SELECT * FROM alembic_version` → `3a65a83e0463` |
| Resume is dead code | `grep cyclic_resume` → only `= False`; setter commented out |
| `force_Stop` typo | `idle.py:33`, `start_vfd.py:22` |
| Full command log | `firmware-production-probe-2026-08-31.txt` |

---

## 19. Area Classification

*Added beyond the requested structure, per §20 of the brief.*

| Area | Classification |
|---|---|
| Fleet inventory, deployed-code identity, config divergence | **VERIFIED FROM PRODUCTION** |
| Management→Firmware boundary (both channels, payload shapes) | **VERIFIED FROM PRODUCTION** |
| Programme derivation and ownership (static + cyclic) | **VERIFIED FROM PRODUCTION** |
| Cyclic open-loop 2.0 s/cycle execution | **VERIFIED FROM PRODUCTION** |
| Firmware→Management result payload | **VERIFIED FROM PRODUCTION** |
| Pass/fail ownership (nobody) | **VERIFIED FROM PRODUCTION** |
| `recovery` = config constant | **VERIFIED FROM PRODUCTION** |
| Seed vs real data separation; gauge-naming provenance | **VERIFIED FROM PRODUCTION** |
| Pressure units (PSF) and duration units (seconds) | **VERIFIED FROM PRODUCTION** |
| Deflection *pipeline* and the *nature* of the defect | **VERIFIED FROM SOURCE ONLY** (arithmetic reproduces production values exactly; gauges offline) |
| Water-infiltration execution as a static hold | **VERIFIED FROM SOURCE ONLY** (+ DB confirms the stage rows) |
| Static execution path (hold, operator VFD control) | **VERIFIED FROM SOURCE ONLY** — last production static run was aborted → **NEEDS T1** |
| Abort semantics (no row posted) | source + one production instance → **NEEDS T3** |
| Broker-disconnect valve/VFD state | **NEEDS CONTROLLED NON-PRODUCTION TEST (T3)** |
| Reboot/power-loss behaviour | **NEEDS CONTROLLED NON-PRODUCTION TEST (T7)** |
| Duplicate command / duplicate POST | **NEEDS CONTROLLED NON-PRODUCTION TEST (T5)** |
| **Deflection scale factor and signedness** | **BLOCKED / UNKNOWN — needs T4 + SICK masters restored** |
| Units of leakage, velocity, area, missile weight | **BLOCKED / UNKNOWN — needs the lab** |
| Whether any `infiltration_tests` row is real | **BLOCKED / UNKNOWN — needs the lab** |
| How turbo valves 5/6 are actually driven | **BLOCKED / UNKNOWN — out of scope** |

**Findings that let us freeze an integration field contract now:** §15 items 1–7, 11, 12, 14 —
the whole requirements side, the units, the direction enum, and the shape of the result payload.

**Findings that require a LabOS-side fix:** the gateway deflection conversion (Q2/T4); a
Pass/Fail owner (Q1); machine-reported completion and the `current_cycle` off-by-one (Q7); an
abort/fault record (Q8); achieved-pressure capture (Q9); splitting `recovery` from the
displacement concept; `system-1`'s config split (Q10); `system-2`'s missing `idle.py` fix (Q11);
idempotency below P1 (§15.13).

**Findings that require Airtable-side action:** the extraction shift (§10.19) — now with a
larger blast radius (§14.1); a machine-readable representation of the design-pressure **pair**
resolving `+60/60` into two unsigned PSF values plus a direction (§15.5); a
water-infiltration-required flag (§15.12); confirmation that no stage-level requirement fields
are expected on the read side (§14.1).

**Findings that require a controlled Stage/E2E test later:** T1–T8, with **T4 first** and
recovery of the `test` node as the precondition for the rest.

---

## 20. Final Decision Summary

*One page for the Airtable / Luis meeting.*

| Question | Production evidence | Decision / conclusion | Owner | Remaining validation |
|---|---|---|---|---|
| Does Management send design pressures or derived stages to Firmware? | MQTT `start` carries only ids; firmware `GET`s the stage; project 78 matches the factor arrays exactly | **Model B via callback pull. Management owns 100% of derivation** | settled | none |
| What must Airtable actually supply? | derivation is deterministic from `inward`/`outward_design_pressure` + `has_water_infiltration` | **Two PSF design pressures, a water-infiltration boolean, identity, target rig. Nothing stage-level** | us → Airtable | Airtable confirms the read-side spec |
| Is one design-pressure field enough? | 36/78 projects (46%) asymmetric; inward drives static-even + cyclic 0–3, outward the rest | **No — two mandatory fields** | Airtable | none |
| How is `+60/60` represented? | boundary carries unsigned magnitudes; direction is a separate enum | **Two unsigned PSF values + `inward`/`outward`. Never a signed number** | Airtable | ratify on the call (contract §10.23) |
| Pressure unit? | `scale:144` PSI→PSF; both rigs log PSF; setpoint compared PSF vs PSF | **PSF everywhere above the sensor. CONFIRMED** | settled | none |
| Duration unit? | `×10` × `sleep(0.1)`; static 30 s, water 900 s, infiltration 321–1692 s | **Seconds. The "minutes" annotation is retired** | settled | none |
| Who computes Passed/Failed? | no writer for `TestResult.result`; 129/129 real trials NULL; the 275 set are seed data | **Nobody. The contract's Pass/Fail has no source** | **IFET + us — decide on the call** | Q1; then a LabOS build |
| Can we export deflection? | stored = `round(raw_uint16_diff × 0.0393701, 2)`; extremes decode to ≈32737 vs int16 max 32767 | **No. Quarantined** — the defect is in the SICK gateway, not firmware | us | **T4** (needs a gauge + masters restored) |
| What is `recovery`? | all 609 real rows = `60` = `recovery_time`; seed rows = `max − perm` | **A config constant in seconds. Not a measurement. Do not map it** | settled | none |
| Why two gauge-naming schemes? | gateway config `1-1…2-8` vs `populate_db.py` `"Gauge 1..4"`; disjoint `test_id` ranges and statistics | **Real vs seed data, not rig generations. Filter on `'^[12]-[1-8]$'`** | settled | none |
| Are cyclic pressures enforced per cycle? | every check commented out; 50 cycles in 101.07 s = 2.021 s/cycle | **No — open loop, time-driven. `low_pressure` is inert** | us | T2 |
| Is static pressure controlled automatically? | `HoldingTimeState` issues no VFD command; browser slider publishes `vfd/command` | **No — the operator is the control loop, unrecorded** | IFET + us | T1 |
| Can we export achieved pressure / duration / cycles completed / timestamps? | no column, no payload field, no computation | **No. All require a LabOS build** | us | Q7, Q9 |
| Are air/water infiltration firmware features? | no infiltration state; water = 900 s static at 0.15 × inward DP; `infiltration_tests` has no write path | **No. Water is a static hold; leakage is never measured** | settled | Q5, T6 |
| Is impact in firmware? | no code path; 39 tests / 114 shots, `shots.result` 72/42 | **No — fully manual, and the only real pass/fail in LabOS** | settled | Q4 (units) |
| Is an aborted test recorded? | `force_stop` skips the POST; `system-2` 2026-08-17 aborted with no row | **No — silent data loss. No abort or fault channel exists** | us | Q8, T3 |
| Is there attempt identity / idempotency today? | no id on any topic or endpoint; `trial_number = len+1`; duplicate POST creates trial 2 | **None. P1's append-only attempt model is a new capability, not a reflection of production** | us | T5 |
| Do both rigs run the same firmware? | byte-identical except `states/idle.py` on `system-2` (missing the RELIEF guard), plus a daily cron restart | **No. A known valve bug is live on `system-2`** | deployment owner | Q11 |
| Is `system-1` correctly configured? | `state_machine` + `valves` on `config1-site-b.json`; `serial_service` on `config1.json` | **No — two configs live in one rig; valve roles/pins come from a site-b file** | deployment owner | Q10, T8 |
| Can deflection be measured at all right now? | both SICK masters unreachable since 2026-08-29 23:08, 45 861 failures | **No — fleet-wide outage. Blocks T4** | IFET | Q12 |
| Can we run any of the recommended tests? | `test` node offline since ~2026-07-24; no non-production rig exists | **No. Recovering `test` is the top infrastructure ask** | IFET (manager) | — |

---

*Read-only audit. No production state was changed. Command log:
`firmware-production-probe-2026-08-31.txt`.*
