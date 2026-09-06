"""
MF harness driver - plays the operator, then asserts the MF properties.

The state machine self-drives once it receives `start`: initializing_valves ->
start_vdf -> holding_time -> relief -> stopping -> recovery -> idle. The one thing it
will not do for itself is raise the pressure: on the real rigs static pressure is an
operator slider, and HoldingTimeState simply waits for the sensor to pass the
setpoint. So this driver sends `start` and then ramps the slider.

It then reads the stub API's ledger and asserts, per delivery-plan MF:

  1. a start carries a run identity, and the trial callback echoes it;
  2. the callback carries a stable event_id;
  3. replaying that exact callback is safe - no second trial is created;
  4. with the pre-MF response shape (RUN_BINDING=off) the callback is recorded
     UNMAPPED, never attached to a guessed run.

Exits non-zero if any assertion fails.
"""
import json
import os
import sys
import time

import paho.mqtt.client as mqtt
import requests

BROKER_HOST = os.environ.get("BROKER_HOST", "mosquitto")
BROKER_PORT = int(os.environ.get("BROKER_PORT", "1883"))
API_BASE = os.environ.get("API_BASE", "http://stub-api:8000")
DEVICE_ID = os.environ.get("DEVICE_ID", "device901")
PROJECT_ID = os.environ.get("PROJECT_ID", "mf-project-1")
TEST_INDEX = os.environ.get("TEST_INDEX", "0")
GAUGES = os.environ.get("GAUGES", "1,2").split(",")

statuses = []
failures = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{(' - ' + detail) if detail else ''}", flush=True)
    if not ok:
        failures.append(name)
    return ok


def wait_for(predicate, timeout, what):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.2)
    print(f"  ... timed out after {timeout}s waiting for {what}", flush=True)
    return False


def main():
    requests.post(f"{API_BASE}/_harness/reset", timeout=10)
    ledger0 = requests.get(f"{API_BASE}/_harness/ledger", timeout=10).json()
    run_binding_on = ledger0["run_binding"]
    print(f"\n== MF harness: stub RUN_BINDING={'on' if run_binding_on else 'off'} ==\n", flush=True)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.on_message = lambda c, u, m: statuses.append(m.payload.decode())
    client.subscribe(f"{DEVICE_ID}/status")
    client.loop_start()
    time.sleep(1.0)

    # 1. The operator picks the work and presses start.
    start = {
        "command": "start",
        "mode": "manual",
        "project_id": PROJECT_ID,
        "test_index": TEST_INDEX,
        "sensor_id": "1",
        "selectedSensors": GAUGES,
    }
    print(f"-> start {json.dumps(start)}", flush=True)
    # The rig is already publishing 'idle' when we attach, so every wait below is
    # measured from here - never against the whole status history.
    mark = len(statuses)
    client.publish(f"{DEVICE_ID}/command", json.dumps(start))

    def since_mark():
        return statuses[mark:]

    if not wait_for(lambda: any(s != 'idle' for s in since_mark()), 60, "the rig to leave idle"):
        print("  rig never left idle; last statuses:", statuses[-10:], flush=True)

    # 2. The operator ramps the slider until the rig says it is tuned/holding.
    freq = 0.0
    while freq < 200 and not any('Holding' in s or 'tuned' in s for s in since_mark()):
        freq += 5.0
        client.publish(
            f"{DEVICE_ID}/vfd/command",
            json.dumps({"command": "set_frequency", "parameter": freq}),
        )
        time.sleep(0.5)
    print(f"-> slider ramped to {freq}", flush=True)

    # 3. The rig finishes on its own: hold -> relief -> stopping -> recovery -> idle.
    #    The trial POST happens in RecoveryState.on_exit, just before Idle is entered,
    #    so wait on the callback landing rather than on the status chip.
    def trial_landed():
        try:
            l = requests.get(f"{API_BASE}/_harness/ledger", timeout=5).json()
            return any(e["kind"].endswith("_trial") for e in l["entries"])
        except Exception:
            return False

    got_trial = wait_for(trial_landed, 180, "the trial callback")
    reached_idle = got_trial and wait_for(
        lambda: any(s == 'idle' for s in statuses[mark + 1:]), 30, "the rig to return to idle")

    ledger = requests.get(f"{API_BASE}/_harness/ledger", timeout=10).json()
    trials = [e for e in ledger["entries"] if e["kind"].endswith("_trial")]
    print(f"\n-- ledger: {len(trials)} trial callback(s), {ledger['deliveries']} delivery record(s)\n", flush=True)
    for e in trials:
        print("   " + json.dumps({k: e[k] for k in ("kind", "outcome", "event_id", "trial_id") if k in e}), flush=True)
    print("", flush=True)

    check("rig returned to idle", reached_idle)
    check("exactly one trial callback arrived", len(trials) == 1, f"got {len(trials)}")
    if not trials:
        return finish()

    trial = trials[0]
    payload = trial["payload"]

    # Property 2: a stable event ID, always.
    event_id = payload.get("event_id")
    check("callback carries an event_id", bool(event_id), str(event_id))

    # The legacy payload must survive unchanged alongside the new keys.
    deflections = payload.get("deflections") or []
    check("callback still carries deflections[]", len(deflections) > 0, f"{len(deflections)} gauge(s)")
    if deflections:
        d = deflections[0]
        check(
            "deflection entry keeps its legacy shape",
            {"deflection_gauge", "max_deflection", "permanent_deflection", "recovery"} <= set(d),
            json.dumps(d),
        )

    if run_binding_on:
        # Property 1: identity threaded from start to callback.
        run = payload.get("run") or {}
        check("callback echoes the run binding", bool(run.get("labos_attempt_id")), json.dumps(run))
        check("callback echoes a stage id", bool(run.get("stage_id")), str(run.get("stage_id")))
        check("backend accepted it against a known run", trial["outcome"] == "ACCEPTED", trial["outcome"])

        # Property 3: replay is safe.
        before = ledger["deliveries"]
        replay = requests.post(
            f"{API_BASE}/projects/{PROJECT_ID}/static_tests/{TEST_INDEX}/trials",
            json=payload,
            timeout=10,
        ).json()
        after = requests.get(f"{API_BASE}/_harness/ledger", timeout=10).json()
        replayed = [e for e in after["entries"] if e.get("outcome") == "REPLAY"]
        check("replaying the exact callback creates nothing new", after["deliveries"] == before,
              f"{before} -> {after['deliveries']}")
        check("replay is recognised as a replay", len(replayed) == 1)
        check("replay returns the first trial id", replay.get("trial_id") == trial.get("trial_id"),
              f"{replay.get('trial_id')} vs {trial.get('trial_id')}")
    else:
        # Property 4: no binding means excluded, not guessed.
        check("pre-MF response yields no run binding", not payload.get("run"), str(payload.get("run")))
        check("backend recorded it UNMAPPED, not guessed", trial["outcome"] == "UNMAPPED", trial["outcome"])

    return finish()


def finish():
    print("", flush=True)
    if failures:
        print(f"== {len(failures)} FAILED: {', '.join(failures)} ==\n", flush=True)
        return 1
    print("== all MF properties hold ==\n", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
