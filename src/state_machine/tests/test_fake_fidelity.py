"""
Fidelity tests: the simulation fakes must produce production-shaped payloads.

A simulated rig proves shape and identity, never physics - fake pressures and
deflections are meaningless numbers. What it must not do is let a type or key bug
pass because the fake was more forgiving than the real thing. These tests pin the
fake SICK gateway to the shape the real one publishes.

Reference: the real gateway's `process_device_data`, in ifet-management
`src/sick_gateway/sick_mqtt_gateway.py`. If that changes, this test should fail.

What this does NOT cover, and needs live evidence to close:
  * whether `recovery` is genuinely always the 60 s constant in production rows;
  * the real value ranges;
  * that the firmware in the running production image matches this working tree.
Those come from a read-only SELECT on management and a hash of the running image.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    'src', 'fake_sick_service'))

import pytest

from api.api import Api

# Field for field, the real gateway's processed_data payload on sick/sensors/{id}.
REAL_GATEWAY_KEYS = {
    "valid", "raw_value", "value", "permanent_value", "offset",
    "zeroed", "assigned_to", "max_value", "units", "timestamp",
}

# The two the state machine forwards straight into the trial POST, as strings.
REAL_GATEWAY_STRING_FIELDS = {"value", "permanent_value", "max_value"}


@pytest.fixture()
def gauge_payload(tmp_path):
    """One published payload from the fake gateway, with a gauge assigned."""
    from fake_sick import FakeSickGateway

    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "device_id": "device901",
        "mqtt": {"broker_host": "localhost", "broker_port": 1883, "username": "", "password": ""},
        "sick": {"gauges": ["1"], "unit": "mm", "poll_interval": 0.2},
    }))
    os.chdir(tmp_path)

    gw = FakeSickGateway(str(config))
    gw.assignments["1"] = "device901"  # assigned, so max/permanent are tracked
    for _ in range(5):
        payload = gw.step("1")
    return payload


def test_fake_publishes_exactly_the_real_gateway_keys(gauge_payload):
    assert set(gauge_payload) == REAL_GATEWAY_KEYS


def test_the_forwarded_fields_are_strings_like_production(gauge_payload):
    """The real gateway formats these with "{:.2f}". A fake sending floats would
    hide a type bug in everything downstream of the trial POST."""
    for field in REAL_GATEWAY_STRING_FIELDS:
        assert isinstance(gauge_payload[field], str), f"{field} must be a string"
        assert gauge_payload[field].count(".") == 1
        assert len(gauge_payload[field].split(".")[1]) == 2, f"{field} needs 2 decimals"


def test_an_unassigned_gauge_reports_free_and_zeroes(tmp_path):
    """The real gateway only tracks max/permanent while a gauge is assigned."""
    from fake_sick import FakeSickGateway

    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "device_id": "device901",
        "mqtt": {"broker_host": "localhost", "broker_port": 1883},
        "sick": {"gauges": ["1"], "unit": "mm"},
    }))
    os.chdir(tmp_path)

    gw = FakeSickGateway(str(config))
    payload = gw.step("1")  # never assigned
    assert payload["assigned_to"] == "free"
    assert payload["max_value"] == "0.00"
    assert payload["permanent_value"] == "0.00"


def test_the_trial_body_survives_the_string_typed_gauge_values(gauge_payload):
    """End of the chain: the strings reach the POST body untouched, not coerced."""
    payload = Api._trial_payload({"1": gauge_payload}, 60)
    entry = payload["deflections"][0]
    assert entry["max_deflection"] == gauge_payload["max_value"]
    assert entry["permanent_deflection"] == gauge_payload["permanent_value"]
    assert isinstance(entry["max_deflection"], str)
    # `recovery` is the config constant, not a measurement.
    assert entry["recovery"] == 60
