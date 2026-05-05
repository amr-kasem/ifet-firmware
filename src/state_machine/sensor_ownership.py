import json
import threading

TOPIC_FMT = 'ifet/firmware/{device_id}/owned-sensors'


def topic(device_id):
    return TOPIC_FMT.format(device_id=device_id)


def publish(client, device_id, sensors):
    """Mark these sensors as owned. Retained — survives broker until cleared."""
    client.publish(
        topic(device_id),
        payload=json.dumps(list(sensors)),
        qos=1,
        retain=True,
    )


def clear(client, device_id):
    """Empty retained payload removes the retention from the broker."""
    client.publish(topic(device_id), payload='', qos=1, retain=True)


def fetch_on_boot(client, device_id, timeout=2.0):
    """
    Subscribe to the ownership topic and wait for the broker to deliver any
    retained payload. Returns the previously-owned sensor list, or [] if
    no retained message exists or the wait times out.

    THREADING REQUIREMENT: the paho network loop must be running on a
    background thread (loop_start()) before calling this. Calling from
    inside on_connect would deadlock — the loop thread that delivers the
    retained message would be blocked waiting on itself.
    """
    result = {'sensors': []}
    received = threading.Event()

    def _on_message(_client, _userdata, msg):
        try:
            if msg.payload:
                result['sensors'] = json.loads(msg.payload.decode())
        except Exception:
            pass
        received.set()

    t = topic(device_id)
    client.message_callback_add(t, _on_message)
    client.subscribe(t, qos=1)
    received.wait(timeout=timeout)
    client.message_callback_remove(t)
    return result['sensors']
