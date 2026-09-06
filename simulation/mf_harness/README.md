# MF harness — an isolated simulated rig

Exercises **run/stage association** end to end without a rig: the delivery plan's **MF**
milestone, closing gaps **G1** (the work order never reaches the rig) and **G2** (the
callback shape has no run, stage or event ID).

## Read this before you bring up any simulated rig

On a workstation running `ifet-management-tunnel.service`, **`127.0.0.1:1883` and
`127.0.0.1:8000` are the production `management` broker and API**, forwarded over SSH.

The older `simulation/ifet_device_node/docker-compose-1.yaml` uses
`network_mode: "host"` with `deployment/config/config1-d.json`, and that config has
`device_id: "device1"`, `broker_host: "localhost"`, `base_url: "http://localhost:8000"`.
Brought up on a tunnelled workstation it therefore attaches a fake rig **impersonating
system-1** to the production broker, publishing `device1/sensors/1` and
`device1/vfd/feedback`, and lets its state machine POST trials into the production
database. Don't use it while the tunnel is up.

This harness cannot reach the tunnel:

| | |
|---|---|
| Networking | private `mf` bridge; services resolve each other by name. **No `network_mode: host`** |
| Host ports | `127.0.0.1:11883` (broker) and `127.0.0.1:18000` (stub API) — never 1883/8000 |
| Rig identity | `device901` / id `901` — not `device1`, `device2` or `test-device` |
| Backend | a stub, not the management service. No database, no Airtable, no rig |

`device_id` must stay `"device" + id`, because `set_vfd_speed` publishes to
`device{self.id}/vfd/command` while the fake VFD subscribes to `{device_id}/vfd/command`.

## Run it

```bash
docker compose -f simulation/mf_harness/docker-compose.yaml up --build -d
docker compose -f simulation/mf_harness/docker-compose.yaml run --rm driver
```

The driver exits non-zero if any MF property fails. To exercise the
backward-compatibility path — a backend that knows nothing about runs:

```bash
RUN_BINDING=off docker compose -f simulation/mf_harness/docker-compose.yaml up -d --force-recreate stub-api
docker compose -f simulation/mf_harness/docker-compose.yaml run --rm driver
```

Tear down with `down -v`. Logs land in `simulation/mf_harness/logs/`, which is
gitignored.

## What is in it

| Service | Role |
|---|---|
| `mosquitto` | the harness broker |
| `stub-api` | the six routes a rig calls, plus the MF run binding. A conformance fixture for the wire contract, **not** a reimplementation of the real API |
| `state_machine_service` | the real firmware, unmodified, from `src/state_machine/` |
| `fake_serial_service` | existing fake — pressure sensor 1 and VFD feedback |
| `fake_valves_service` | existing fake — valve status |
| `fake_sick_service` | **new** — the deflection gauges. The two existing fakes never covered `sick/sensors/{n}`, so no simulated rig could complete a test before this |
| `driver` | plays the operator (start, then ramp the slider), then asserts the MF properties |

`fake_sick_service` mirrors the real gateway's payload field for field, including
`max_value`/`permanent_value` arriving as **strings** — the state machine forwards them
straight into the trial POST, so a fake that sent numbers would hide a type bug.

The driver has to ramp the VFD because on the real rigs **static pressure is an
operator slider**: `HoldingTimeState` waits for the sensor to pass the setpoint and
never drives the VFD itself. See
`docs/labos-airtable/evidence/firmware-production-runtime-contract-2026-08-31.md`.

## The wire contract it fixes

`GET /projects/{pid}/static-tests/{idx}` and `GET /projects/{pid}/next-cyclic-test`
gain an optional `run` object, minted server-side:

```json
{"index": 0, "type": "outward", "pressure": 60.0, "duration": 10,
 "run": {"labos_attempt_id": "…", "programme_id": "…",
         "stage_id": "stg-static-0", "stage_ordinal": 1}}
```

The rig echoes it back on the trial POST, with a stage event ID it minted at start:

```json
{"deflections": [{"deflection_gauge": "1", "max_deflection": "12.34",
                  "permanent_deflection": "1.20", "recovery": 60}],
 "event_id": "…", "run": { … }}
```

Three properties follow, and the real backend must honour all three:

1. **Identity is resolved server-side.** The MQTT `start` payload is unchanged, so MF
   needs no UI release, and cyclic — which has no `test_index` at start and already
   picks the test server-side via `next-cyclic-test` — works the same way.
2. **`event_id` is minted per stage attempt and reused across POST retries.** That is
   what makes a retry a replay instead of a second trial. A rerun of the same stage is
   a new attempt and gets a new ID.
3. **No binding means unmapped, never guessed.** With no `run` in the response the
   callback goes out in the legacy shape and the backend records it as unmapped. The
   rig clears any previous binding at every start, so a stale attempt ID cannot ride
   along on a later callback.

Both `run` and `event_id` are omitted entirely when absent, so a pre-MF backend
receives byte-for-byte the body it receives today.
