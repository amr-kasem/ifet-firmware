"""
Stub of the management report-api, for the MF harness only.

It implements exactly the six routes a rig calls, and nothing else. It exists so the
firmware side of MF (run/stage association - delivery-plan gaps G1 and G2) can be
developed and replayed on a workstation without the management service, a database,
or any reachable rig.

It is deliberately NOT a reimplementation of the real API. It is a conformance
fixture for the wire contract, and it asserts the two MF properties that the real
backend must also honour:

  * a trial POST is keyed on `event_id`, so a replay returns the first result and
    creates nothing (idempotency);
  * a trial POST with no `run` binding is recorded as UNMAPPED rather than attached
    to a guessed run.

`RUN_BINDING=off` makes the stub answer like today's production API - no `run` key at
all - which is how the backward-compatibility path gets tested.
"""
import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="MF harness stub API")

# When off, responses omit `run` entirely: the pre-MF production shape.
RUN_BINDING = os.environ.get("RUN_BINDING", "on").lower() not in ("off", "0", "false")

# Static fixture: one project, two static stages, one cyclic test.
PROJECT_ID = os.environ.get("STUB_PROJECT_ID", "mf-project-1")

# The fake pressure sensor's transfer function is `vfd_frequency * 0.1`, so these
# defaults are chosen to be reachable by the harness driver at a plausible VFD
# frequency - not for physical realism. Identity threading is what is under test.
PRESSURE = float(os.environ.get("STUB_PRESSURE", "5.0"))
DURATION = int(os.environ.get("STUB_DURATION", "2"))
PROGRAMME_ID = "prg-" + uuid.uuid5(uuid.NAMESPACE_URL, "mf/programme/1").hex[:12]
ATTEMPT_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, "mf/attempt/1"))

STATIC_TESTS = {
    "0": {"index": 0, "type": "outward", "pressure": PRESSURE, "duration": DURATION},
    "1": {"index": 1, "type": "inward", "pressure": PRESSURE, "duration": DURATION},
}
CYCLIC_TESTS = {
    "0": {
        "index": 0,
        "type": "outward",
        "high_pressure": PRESSURE,
        "low_pressure": PRESSURE / 4,
        "cycles": 3,
        "current_cycle": 0,
    },
}

# event_id -> the response first returned for it. The replay ledger.
DELIVERIES = {}
# Everything received, in order, including unmapped and replayed calls.
LEDGER = []


def _log(kind, payload, outcome, **extra):
    entry = {
        "kind": kind,
        "at": datetime.now(timezone.utc).isoformat(),
        "outcome": outcome,
        "payload": payload,
        **extra,
    }
    LEDGER.append(entry)
    print(json.dumps(entry), flush=True)
    return entry


def _run_binding(stage_key, stage_kind):
    """The MF addition: identity the rig echoes back, minted server-side."""
    if not RUN_BINDING:
        return None
    return {
        "labos_attempt_id": ATTEMPT_ID,
        "programme_id": PROGRAMME_ID,
        "stage_id": f"stg-{stage_kind}-{stage_key}",
        "stage_ordinal": int(stage_key) + 1,
    }


@app.get("/devices/{device_id}")
def get_device(device_id: str):
    # `turbo_charger: None` keeps the simulated rig a standalone master.
    return {"id": device_id, "turbo_charger": None, "status": "idle"}


@app.get("/projects/{project_id}/static-tests/{static_test_index}/")
@app.get("/projects/{project_id}/static-tests/{static_test_index}")
def get_static_test(project_id: str, static_test_index: str):
    test = dict(STATIC_TESTS.get(str(static_test_index), STATIC_TESTS["0"]))
    run = _run_binding(str(static_test_index), "static")
    if run:
        test["run"] = run
    return test


@app.get("/projects/{project_id}/next-cyclic-test")
def next_cyclic_test(project_id: str):
    test = dict(CYCLIC_TESTS["0"])
    run = _run_binding("0", "cyclic")
    if run:
        test["run"] = run
    return test


@app.put("/projects/{project_id}/cyclic_tests/{cyclic_test_index}/start")
def start_cyclic(project_id: str, cyclic_test_index: str):
    return {"status": "started", "index": cyclic_test_index}


@app.put("/projects/{project_id}/cyclic_tests/{cyclic_test_index}/update_status")
async def update_cyclic(project_id: str, cyclic_test_index: str, request: Request):
    body = await request.body()
    return {"status": "updated", "body": body.decode() or None}


async def _receive_trial(kind, project_id, test_index, request):
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    event_id = payload.get("event_id")
    run = payload.get("run")

    # Replay: the same event_id returns the first answer and creates nothing.
    if event_id and event_id in DELIVERIES:
        first = DELIVERIES[event_id]
        _log(kind, payload, "REPLAY", event_id=event_id, trial_id=first["trial_id"])
        return JSONResponse(first)

    # No binding: recorded, excluded, never attached to a guessed run.
    if not run or not run.get("labos_attempt_id"):
        entry = _log(kind, payload, "UNMAPPED", event_id=event_id)
        result = {
            "trial_id": None,
            "delivery": "unmapped",
            "reason": "no run binding on the callback; preserved and excluded",
            "received_at": entry["at"],
        }
        if event_id:
            DELIVERIES[event_id] = result
        return JSONResponse(result, status_code=202)

    trial_id = f"trial-{len(DELIVERIES) + 1}"
    result = {
        "trial_id": trial_id,
        "delivery": "accepted",
        "labos_attempt_id": run["labos_attempt_id"],
        "stage_id": run.get("stage_id"),
        "deflection_count": len(payload.get("deflections") or []),
    }
    if event_id:
        DELIVERIES[event_id] = result
    _log(kind, payload, "ACCEPTED", event_id=event_id, trial_id=trial_id)
    return JSONResponse(result)


@app.post("/projects/{project_id}/static_tests/{static_test_index}/trials")
async def static_trial(project_id: str, static_test_index: str, request: Request):
    return await _receive_trial("static_trial", project_id, static_test_index, request)


@app.post("/projects/{project_id}/cyclic-tests/{cyclic_test_index}/trials")
async def cyclic_trial(project_id: str, cyclic_test_index: str, request: Request):
    return await _receive_trial("cyclic_trial", project_id, cyclic_test_index, request)


# --- harness introspection, not part of the contract -------------------------


@app.get("/_harness/ledger")
def ledger():
    return {
        "run_binding": RUN_BINDING,
        "deliveries": len(DELIVERIES),
        "entries": LEDGER,
    }


@app.post("/_harness/reset")
def reset():
    DELIVERIES.clear()
    LEDGER.clear()
    return {"reset": True}
