"""
Unit tests: MF run/stage association (delivery-plan MF, gaps G1 and G2).

No broker and no API needed - these cover the wire contract and the binding rules.
The end-to-end path is exercised by simulation/mf_harness.

The properties under test:
  * a start binds the run identity the backend handed us, and mints one stage event ID;
  * a start with no `run` in the response clears any previous binding, so a callback
    can never carry a stale attempt ID;
  * the trial body is byte-for-byte the legacy body when there is no binding;
  * a retried POST reuses the same body, so the backend sees a replay, not a new trial.
"""
import logging
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

from api.api import Api, TRIAL_POST_ATTEMPTS
from state_machine import StateMachine


GAUGES = {
    "1": {"max_value": "12.34", "permanent_value": "1.20"},
    "2": {"max_value": "-3.00", "permanent_value": "0.00"},
}

BINDING = {
    "labos_attempt_id": "6f1c2e5a-0000-4000-8000-000000000001",
    "programme_id": "prg-abc123",
    "stage_id": "stg-static-0",
    "stage_ordinal": 1,
}


def binder():
    """A stand-in for the machine, so bind_run can be tested without a broker."""
    fake = MagicMock()
    fake.logger = logging.getLogger("test-binder")
    return fake


# --- binding rules -----------------------------------------------------------


def test_bind_run_takes_the_backend_identity_and_mints_an_event_id():
    fake = binder()
    returned = StateMachine.bind_run(fake, {"index": 0, "pressure": 60.0, "run": BINDING})

    assert returned == BINDING
    assert fake.run_binding == BINDING
    assert fake.stage_event_id  # minted
    # A UUID, not the attempt ID reused.
    assert fake.stage_event_id != BINDING["labos_attempt_id"]


def test_a_start_with_no_run_clears_a_previous_binding():
    """The G2 rule: an unmapped callback is excluded, never guessed into a run."""
    fake = binder()
    StateMachine.bind_run(fake, {"run": BINDING})
    assert fake.run_binding == BINDING

    StateMachine.bind_run(fake, {"index": 1, "pressure": 60.0})  # pre-MF response
    assert fake.run_binding is None
    assert fake.stage_event_id  # still minted, so the callback is still identifiable


@pytest.mark.parametrize("response", [
    {},
    {"run": None},
    {"run": {}},
    {"run": {"stage_id": "stg-static-0"}},          # no attempt id
    {"run": {"labos_attempt_id": ""}},              # empty attempt id
    {"run": "6f1c2e5a"},                            # wrong type
    None,                                           # not a dict at all
    "unavailable",
])
def test_incomplete_bindings_are_refused(response):
    fake = binder()
    assert StateMachine.bind_run(fake, response) is None
    assert fake.run_binding is None


def test_each_stage_attempt_gets_its_own_event_id():
    fake = binder()
    StateMachine.bind_run(fake, {"run": BINDING})
    first = fake.stage_event_id
    StateMachine.bind_run(fake, {"run": BINDING})
    assert fake.stage_event_id != first, "a rerun is a new attempt, not a replay"


# --- wire contract -----------------------------------------------------------


def test_payload_without_a_binding_is_exactly_the_legacy_body():
    payload = Api._trial_payload(GAUGES, 60)
    assert payload == {
        "deflections": [
            {"deflection_gauge": "1", "max_deflection": "12.34",
             "permanent_deflection": "1.20", "recovery": 60},
            {"deflection_gauge": "2", "max_deflection": "-3.00",
             "permanent_deflection": "0.00", "recovery": 60},
        ]
    }
    assert "run" not in payload and "event_id" not in payload


def test_payload_with_a_binding_adds_run_and_event_id_and_keeps_deflections():
    payload = Api._trial_payload(GAUGES, 60, run=BINDING, event_id="evt-1")
    assert payload["run"] == BINDING
    assert payload["event_id"] == "evt-1"
    assert len(payload["deflections"]) == 2
    assert payload["deflections"][0]["max_deflection"] == "12.34"


def test_an_event_id_is_sent_even_when_the_run_is_unbound():
    """An unmapped callback still has to be identifiable, or a retry duplicates it."""
    payload = Api._trial_payload(GAUGES, 60, run=None, event_id="evt-1")
    assert payload["event_id"] == "evt-1"
    assert "run" not in payload


# --- retry is a replay, not a second trial -----------------------------------


def test_finish_static_test_posts_the_binding_to_the_trials_route():
    api = Api(api="http://stub:8000")
    with patch("api.api.requests.post") as post:
        post.return_value = MagicMock(json=lambda: {"trial_id": "t1"}, raise_for_status=lambda: None)
        api.finish_static_test("p1", "0", GAUGES, 60, run=BINDING, event_id="evt-1")

    url, kwargs = post.call_args[0][0], post.call_args[1]
    assert url == "http://stub:8000/projects/p1/static_tests/0/trials"
    assert kwargs["json"]["run"] == BINDING
    assert kwargs["json"]["event_id"] == "evt-1"


def test_finish_cyclic_test_posts_the_binding_to_the_cyclic_route():
    api = Api(api="http://stub:8000")
    with patch("api.api.requests.post") as post:
        post.return_value = MagicMock(json=lambda: {"trial_id": "t1"}, raise_for_status=lambda: None)
        api.finish_cyclic_test("p1", "0", GAUGES, 0, run=BINDING, event_id="evt-2")

    url, kwargs = post.call_args[0][0], post.call_args[1]
    assert url == "http://stub:8000/projects/p1/cyclic-tests/0/trials"
    assert kwargs["json"]["event_id"] == "evt-2"


def test_a_retry_resends_an_identical_body():
    """Same event_id on every attempt: that is what the backend dedupes on."""
    api = Api(api="http://stub:8000")
    ok = MagicMock(json=lambda: {"trial_id": "t1"}, raise_for_status=lambda: None)

    with patch("api.api.requests.post") as post, patch("api.api.time.sleep"):
        post.side_effect = [ConnectionError("boom"), ok]
        api.finish_static_test("p1", "0", GAUGES, 60, run=BINDING, event_id="evt-1")

    assert post.call_count == 2
    bodies = [c[1]["json"] for c in post.call_args_list]
    assert bodies[0] == bodies[1], "a retry must not mint a new event_id"
    assert bodies[0]["event_id"] == "evt-1"


def test_a_lost_trial_stays_loud():
    """Missing telemetry must never read as a completed stage."""
    api = Api(api="http://stub:8000")
    with patch("api.api.requests.post") as post, patch("api.api.time.sleep"):
        post.side_effect = ConnectionError("boom")
        with pytest.raises(ConnectionError):
            api.finish_static_test("p1", "0", GAUGES, 60, run=BINDING, event_id="evt-1")

    assert post.call_count == TRIAL_POST_ATTEMPTS
