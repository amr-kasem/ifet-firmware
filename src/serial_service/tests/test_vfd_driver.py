import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from vfd_handler.vfd_driver import (
    COMMAND_RUN_FORWARD,
    COMMAND_RUN_REVERSE,
    COMMAND_STOP,
    REG_DC_BUS_VOLTAGE,
    REG_FREQUENCY_COMMAND,
    REG_OPERATION_COMMAND,
    REG_OUTPUT_CURRENT,
    REG_OUTPUT_FREQUENCY,
    REG_OUTPUT_VOLTAGE,
    ModbusTCPTransport,
    VFDDriver,
)


class FakeTransport:
    def __init__(self, reads=None):
        self.reads = reads or {}
        self.writes = []

    def connect(self):
        pass

    def close(self):
        pass

    def read_register(self, address, count=1):
        return self.reads[address]

    def write_register(self, address, value):
        self.writes.append((address, value))


def test_set_frequency_hz_writes_scaled_value_for_5hz():
    transport = FakeTransport()
    driver = VFDDriver(transport)

    driver.set_frequency_hz(5.0)

    assert transport.writes == [(REG_FREQUENCY_COMMAND, 500)]


def test_set_frequency_hz_writes_scaled_value_for_50hz():
    transport = FakeTransport()
    driver = VFDDriver(transport)

    driver.set_frequency_hz(50.0)

    assert transport.writes == [(REG_FREQUENCY_COMMAND, 5000)]


def test_run_forward_writes_delta_forward_command():
    transport = FakeTransport()
    driver = VFDDriver(transport)

    driver.run_forward()

    assert transport.writes == [(REG_OPERATION_COMMAND, COMMAND_RUN_FORWARD)]


def test_run_reverse_writes_delta_reverse_command():
    transport = FakeTransport()
    driver = VFDDriver(transport)

    driver.run_reverse()

    assert transport.writes == [(REG_OPERATION_COMMAND, COMMAND_RUN_REVERSE)]


def test_stop_writes_delta_stop_command():
    transport = FakeTransport()
    driver = VFDDriver(transport)

    driver.stop()

    assert transport.writes == [(REG_OPERATION_COMMAND, COMMAND_STOP)]


def test_read_output_frequency_hz_reads_monitor_and_scales_value():
    transport = FakeTransport({REG_OUTPUT_FREQUENCY: 1234})
    driver = VFDDriver(transport)

    assert driver.read_output_frequency_hz() == 12.34


def test_read_output_current_reads_current_register():
    transport = FakeTransport({REG_OUTPUT_CURRENT: 42})
    driver = VFDDriver(transport)

    assert driver.read_output_current() == 42


def test_read_dc_bus_voltage_reads_voltage_register():
    transport = FakeTransport({REG_DC_BUS_VOLTAGE: 680})
    driver = VFDDriver(transport)

    assert driver.read_dc_bus_voltage() == 680


def test_read_output_voltage_reads_output_voltage_register():
    transport = FakeTransport({REG_OUTPUT_VOLTAGE: 220})
    driver = VFDDriver(transport)

    assert driver.read_output_voltage() == 220


class FakeResponse:
    def __init__(self, registers=None):
        self.registers = registers or []

    def isError(self):
        return False


class FakeTcpClient:
    def __init__(self):
        self.connected = False
        self.connect_calls = 0
        self.close_calls = 0
        self.reads = []
        self.writes = []

    def connect(self):
        self.connect_calls += 1
        self.connected = True
        return True

    def close(self):
        self.close_calls += 1
        self.connected = False

    def read_holding_registers(self, register, count=1, slave=1):
        self.reads.append((register, count, slave))
        return FakeResponse([123])

    def write_register(self, register, value, device_id=1):
        self.writes.append((register, value, device_id))
        return FakeResponse()


def test_tcp_transport_reuses_connection_across_operations():
    client = FakeTcpClient()
    transport = ModbusTCPTransport(host="192.0.2.10", port=502, unit_id=7, client=client)

    transport.write_register(REG_OPERATION_COMMAND, COMMAND_RUN_FORWARD)
    transport.read_register(REG_OUTPUT_FREQUENCY)
    transport.write_register(REG_FREQUENCY_COMMAND, 500)

    assert client.connect_calls == 1
    assert client.writes == [
        (REG_OPERATION_COMMAND, COMMAND_RUN_FORWARD, 7),
        (REG_FREQUENCY_COMMAND, 500, 7),
    ]
    assert client.reads == [(REG_OUTPUT_FREQUENCY, 1, 7)]
