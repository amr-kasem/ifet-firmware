import logging
import os


REG_OPERATION_COMMAND = 0x2000
REG_FREQUENCY_COMMAND = 0x2001
REG_FAULT_CODE = 0x2100
REG_OPERATION_STATUS = 0x2101
REG_FREQUENCY_COMMAND_MONITOR = 0x2102
REG_OUTPUT_FREQUENCY = 0x2103
REG_OUTPUT_CURRENT = 0x2104
REG_DC_BUS_VOLTAGE = 0x2105
REG_OUTPUT_VOLTAGE = 0x2106

COMMAND_STOP = 0x0001
COMMAND_RUN_FORWARD = 0x0012
COMMAND_RUN_REVERSE = 0x0022

READ_HOLDING_REGISTERS = 3
WRITE_SINGLE_REGISTER = 6


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class ModbusRTUTransport:
    """VFD transport adapter over the existing shared SerialCom bus."""

    def __init__(self, modbus_com, unit_id, close_underlying=False):
        if modbus_com is None:
            raise ValueError("modbus_com is required for serial VFD transport")
        self.modbus_com = modbus_com
        self.unit_id = int(unit_id)
        self.close_underlying = close_underlying

    def connect(self):
        """SerialCom opens the port lazily through minimalmodbus."""

    def close(self):
        if self.close_underlying:
            self.modbus_com.close()

    def read_register(self, address, count=1):
        result = self.modbus_com.read_register(
            self.unit_id,
            address,
            count,
            READ_HOLDING_REGISTERS,
        )
        return _normalize_register_result(result, count)

    def write_register(self, address, value):
        self.modbus_com.write_register(
            self.unit_id,
            address,
            int(value),
            0,
            WRITE_SINGLE_REGISTER,
        )


class ModbusTCPTransport:
    """Persistent Modbus TCP transport for Delta C2000 Plus VFD control."""

    def __init__(
        self,
        host,
        port=502,
        unit_id=1,
        timeout=2.0,
        client=None,
        client_factory=None,
    ):
        if not host:
            raise ValueError("host is required for TCP VFD transport")
        self.host = host
        self.port = int(port)
        self.unit_id = int(unit_id)
        self.timeout = float(timeout)
        self.client = client or self._build_client(client_factory)

    def _build_client(self, client_factory):
        if client_factory is not None:
            return client_factory(host=self.host, port=self.port, timeout=self.timeout)

        from pymodbus.client import ModbusTcpClient

        return ModbusTcpClient(host=self.host, port=self.port, timeout=self.timeout)

    def connect(self):
        if getattr(self.client, "connected", False):
            return
        if not self.client.connect():
            raise ConnectionError(f"Failed to connect to VFD at {self.host}:{self.port}")

    def close(self):
        if getattr(self.client, "connected", False):
            self.client.close()

    def read_register(self, address, count=1):
        self.connect()
        try:
            result = self.client.read_holding_registers(
                address,
                count=count,
                slave=self.unit_id,
            )
        except Exception:
            self.close()
            raise
        if result.isError():
            self.close()
            raise IOError(f"Failed to read VFD register {address}")
        return _normalize_register_result(result.registers, count)

    def write_register(self, address, value):
        self.connect()
        try:
            result = self.client.write_register(
                address,
                int(value),
                device_id=self.unit_id,
            )
        except TypeError:
            result = self.client.write_register(
                address,
                int(value),
                slave=self.unit_id,
            )
        except Exception:
            self.close()
            raise
        if result.isError():
            self.close()
            raise IOError(f"Failed to write VFD register {address}")


class DryRunTransport:
    """No-hardware transport that logs control operations and returns zeros."""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.writes = []

    def connect(self):
        self.logger.info("VFD dry-run transport connected")

    def close(self):
        self.logger.info("VFD dry-run transport closed")

    def read_register(self, address, count=1):
        self.logger.info("VFD dry-run read register %s count %s", address, count)
        if count == 1:
            return 0
        return [0] * count

    def write_register(self, address, value):
        self.writes.append((address, int(value)))
        self.logger.warning("VFD dry-run write register %s value %s", address, value)


class VFDDriver:
    """High-level Delta C2000 Plus VFD API independent of Modbus transport."""

    def __init__(self, transport):
        self.transport = transport

    def connect(self):
        self.transport.connect()

    def close(self):
        self.transport.close()

    def read_register(self, address, count=1):
        return self.transport.read_register(address, count)

    def write_register(self, address, value):
        self.transport.write_register(address, value)

    def set_frequency_hz(self, hz):
        scaled_hz = int(round(float(hz) * 100))
        self.write_register(REG_FREQUENCY_COMMAND, scaled_hz)

    def run_forward(self):
        self.write_register(REG_OPERATION_COMMAND, COMMAND_RUN_FORWARD)

    def run_reverse(self):
        self.write_register(REG_OPERATION_COMMAND, COMMAND_RUN_REVERSE)

    def stop(self):
        self.write_register(REG_OPERATION_COMMAND, COMMAND_STOP)

    def read_status(self):
        return self.read_register(REG_OPERATION_STATUS)

    def read_fault_code(self):
        return self.read_register(REG_FAULT_CODE)

    def read_output_frequency_hz(self):
        return self.read_register(REG_OUTPUT_FREQUENCY) / 100.0

    def read_output_current(self):
        return self.read_register(REG_OUTPUT_CURRENT)

    def read_dc_bus_voltage(self):
        return self.read_register(REG_DC_BUS_VOLTAGE)

    def read_output_voltage(self):
        return self.read_register(REG_OUTPUT_VOLTAGE)


def build_vfd_driver(config, serial_com=None, logger=None):
    vfd_config = config.get("vfd", {})
    unit_id = int(
        vfd_config.get(
            "unit_id",
            vfd_config.get("address", os.getenv("VFD_UNIT_ID", 1)),
        )
    )
    enabled = _as_bool(vfd_config.get("enabled", os.getenv("VFD_ENABLED")), True)
    dry_run = _as_bool(vfd_config.get("dry_run", os.getenv("VFD_DRY_RUN")), False)

    if not enabled or dry_run:
        return VFDDriver(DryRunTransport(logger=logger))

    transport_name = str(
        vfd_config.get("transport", os.getenv("VFD_TRANSPORT", "serial"))
    ).strip().lower()

    if transport_name == "serial":
        return VFDDriver(ModbusRTUTransport(serial_com, unit_id))
    if transport_name == "tcp":
        tcp_config = vfd_config.get("tcp", {})
        host = tcp_config.get("host", os.getenv("VFD_TCP_HOST"))
        port = tcp_config.get("port", os.getenv("VFD_TCP_PORT", 502))
        timeout = tcp_config.get(
            "timeout",
            vfd_config.get("timeout", os.getenv("VFD_TIMEOUT_SECONDS", 2.0)),
        )
        return VFDDriver(
            ModbusTCPTransport(
                host=host,
                port=port,
                unit_id=unit_id,
                timeout=timeout,
            )
        )

    raise ValueError(f"Unsupported VFD transport: {transport_name}")


def _normalize_register_result(result, count):
    if count == 1 and isinstance(result, (list, tuple)):
        return result[0]
    return result
