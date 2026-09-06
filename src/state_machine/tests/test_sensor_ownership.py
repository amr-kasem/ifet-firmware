"""
Tests for sensor_ownership module.
Runs against the live broker at localhost:1883.
Each test uses a unique device_id to avoid cross-test retained-message pollution.
"""
import json
import threading
import time
import uuid

import paho.mqtt.client as mqtt
import pytest

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import sensor_ownership

# These tests PUBLISH to the broker they are pointed at. On a workstation running
# ifet-management-tunnel.service, localhost:1883 is the PRODUCTION broker - so the
# host and port are overridable, and the harness broker is the safe target:
#   IFET_TEST_BROKER_HOST=127.0.0.1 IFET_TEST_BROKER_PORT=11883 pytest
BROKER_HOST = os.environ.get("IFET_TEST_BROKER_HOST", "localhost")
BROKER_PORT = int(os.environ.get("IFET_TEST_BROKER_PORT", "1883"))


def make_client(on_connect=None, on_message=None):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if on_connect:
        c.on_connect = on_connect
    if on_message:
        c.on_message = on_message
    c.connect(BROKER_HOST, BROKER_PORT)
    c.loop_start()
    return c


def wait_connected(c, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if c.is_connected():
            return True
        time.sleep(0.05)
    return False


@pytest.fixture()
def client():
    connected = threading.Event()

    def _on_connect(c, userdata, flags, rc, props):
        if rc == 0:
            connected.set()

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_connect = _on_connect
    c.connect(BROKER_HOST, BROKER_PORT)
    c.loop_start()
    assert connected.wait(5), "Could not connect to broker"
    yield c
    c.loop_stop()
    c.disconnect()


@pytest.fixture()
def device_id():
    return f"test-device-{uuid.uuid4().hex[:8]}"


# ── publish & clear ──────────────────────────────────────────────────────────

def test_publish_stores_sensors_as_retained(client, device_id):
    sensors = ["sensor-A", "sensor-B"]
    sensor_ownership.publish(client, device_id, sensors)
    time.sleep(0.2)  # let broker acknowledge

    received = {}
    got = threading.Event()

    def _on_msg(c, u, msg):
        if msg.topic == sensor_ownership.topic(device_id):
            received['payload'] = msg.payload
            got.set()

    spy = make_client()
    spy.on_message = _on_msg
    spy.subscribe(sensor_ownership.topic(device_id), qos=1)
    assert got.wait(3), "No retained message delivered"
    assert json.loads(received['payload'].decode()) == sensors
    spy.loop_stop(); spy.disconnect()


def test_clear_removes_retained_payload(client, device_id):
    sensor_ownership.publish(client, device_id, ["s1"])
    time.sleep(0.2)
    sensor_ownership.clear(client, device_id)
    time.sleep(0.2)

    received_payloads = []
    done = threading.Event()

    def _on_msg(c, u, msg):
        received_payloads.append(msg.payload)
        done.set()

    spy = make_client()
    spy.on_message = _on_msg
    spy.subscribe(sensor_ownership.topic(device_id), qos=1)
    # Give broker 1s to deliver any retained — if none, that's the success
    done.wait(1.0)
    # Either no message, or the retained message is empty
    assert all(p == b'' for p in received_payloads), \
        f"Expected empty/no retained, got: {received_payloads}"
    spy.loop_stop(); spy.disconnect()


# ── fetch_on_boot ─────────────────────────────────────────────────────────────

def test_fetch_on_boot_returns_previously_owned_sensors(client, device_id):
    sensors = ["sensor-X", "sensor-Y"]
    sensor_ownership.publish(client, device_id, sensors)
    time.sleep(0.2)

    # fetch_on_boot uses a *separate* client so it gets the retained on subscribe
    c2 = make_client()
    assert wait_connected(c2)
    result = sensor_ownership.fetch_on_boot(c2, device_id)
    assert result == sensors
    c2.loop_stop(); c2.disconnect()


def test_fetch_on_boot_returns_empty_when_no_retained(device_id):
    c = make_client()
    assert wait_connected(c)
    result = sensor_ownership.fetch_on_boot(c, device_id, timeout=0.5)
    assert result == []
    c.loop_stop(); c.disconnect()


def test_fetch_on_boot_returns_empty_after_clear(client, device_id):
    sensor_ownership.publish(client, device_id, ["s1", "s2"])
    time.sleep(0.2)
    sensor_ownership.clear(client, device_id)
    time.sleep(0.2)

    c2 = make_client()
    assert wait_connected(c2)
    result = sensor_ownership.fetch_on_boot(c2, device_id, timeout=1.0)
    assert result == []
    c2.loop_stop(); c2.disconnect()


def test_publish_overwrites_previous_ownership(client, device_id):
    sensor_ownership.publish(client, device_id, ["old-sensor"])
    time.sleep(0.1)
    sensor_ownership.publish(client, device_id, ["new-sensor"])
    time.sleep(0.2)

    c2 = make_client()
    assert wait_connected(c2)
    result = sensor_ownership.fetch_on_boot(c2, device_id)
    assert result == ["new-sensor"]
    c2.loop_stop(); c2.disconnect()
