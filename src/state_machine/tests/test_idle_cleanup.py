"""
Integration test: IdleState.on_enter releases sensors and clears ownership.
Simulates both normal and boot-recovery paths.
"""
import json
import threading
import time
import uuid
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import paho.mqtt.client as mqtt
import pytest
import sensor_ownership

# These tests PUBLISH to the broker they are pointed at. On a workstation running
# ifet-management-tunnel.service, localhost:1883 is the PRODUCTION broker - so the
# host and port are overridable, and the harness broker is the safe target:
#   IFET_TEST_BROKER_HOST=127.0.0.1 IFET_TEST_BROKER_PORT=11883 pytest
BROKER_HOST = os.environ.get("IFET_TEST_BROKER_HOST", "localhost")
BROKER_PORT = int(os.environ.get("IFET_TEST_BROKER_PORT", "1883"))


def make_connected_client():
    connected = threading.Event()
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    c.on_connect = lambda *_: connected.set()
    c.connect(BROKER_HOST, BROKER_PORT)
    c.loop_start()
    assert connected.wait(5), "Broker unreachable"
    return c


@pytest.fixture()
def device_id():
    return f"test-idle-{uuid.uuid4().hex[:8]}"


def collect_topic(client, topic_pattern, duration=1.5):
    """Collect all messages on a topic for `duration` seconds."""
    msgs = []
    client.message_callback_add(topic_pattern, lambda c, u, m: msgs.append(m))
    client.subscribe(topic_pattern, qos=1)
    time.sleep(duration)
    return msgs


def test_idle_on_enter_releases_sensors_and_clears_ownership(device_id):
    """
    After IdleState.on_enter: sick/release published for each sensor,
    ownership topic cleared, selected_deflection_sensors reset to [].
    """
    from unittest.mock import MagicMock

    sensors = ["s1", "s2"]
    client = make_connected_client()

    # Pre-seed ownership (simulates mid-test state)
    sensor_ownership.publish(client, device_id, sensors)
    time.sleep(0.2)

    # Spy on sick/release traffic
    releases = []
    client.message_callback_add('sick/release/#', lambda c, u, m: releases.append(m.topic))
    client.subscribe('sick/release/#', qos=1)

    # Spy on ownership topic
    ownership_payloads = []
    client.message_callback_add(
        sensor_ownership.topic(device_id),
        lambda c, u, m: ownership_payloads.append(m.payload)
    )
    client.subscribe(sensor_ownership.topic(device_id), qos=1)

    # Build a minimal mock machine and run IdleState.on_enter
    machine = MagicMock()
    machine.client = client
    machine.device_id = device_id
    machine.selected_deflection_sensors = sensors
    machine.selected_deflection_sensors_topics = [f'sick/sensors/{s}' for s in sensors]
    machine.valves = []  # skip valve loop
    machine.task = None

    from states.idle import IdleState
    idle = IdleState(machine)
    idle.on_enter()

    time.sleep(0.5)

    # sick/release published for each sensor
    released = [t.split('/')[-1] for t in releases]
    assert 's1' in released, f"Expected s1 in releases, got: {releases}"
    assert 's2' in released, f"Expected s2 in releases, got: {releases}"

    # ownership topic cleared (empty payload)
    assert any(p == b'' for p in ownership_payloads), \
        f"Expected empty ownership clear, got: {ownership_payloads}"

    # in-memory list reset
    assert machine.selected_deflection_sensors == []

    client.loop_stop()
    client.disconnect()


def test_idle_on_enter_safe_on_first_boot_no_sensors(device_id):
    """IdleState.on_enter must not raise when no sensors have been assigned yet."""
    from unittest.mock import MagicMock
    from states.idle import IdleState

    client = make_connected_client()

    machine = MagicMock()
    machine.client = client
    machine.device_id = device_id
    machine.selected_deflection_sensors = []
    machine.selected_deflection_sensors_topics = []
    machine.valves = []
    machine.task = None

    idle = IdleState(machine)
    idle.on_enter()  # must not raise

    client.loop_stop()
    client.disconnect()
