import os
import time
import minimalmodbus
import serial
import json
import threading
import logging
from logging.handlers import RotatingFileHandler
from typing import Union
from .modbus_com import ModbusCom

# Transient bus faults that are safe to retry within a single locked transaction.
# These cover the symptoms seen in the field: corrupted/truncated frames
# (InvalidResponseError -> "Checksum error", "Too short ... response") and
# missing replies (NoResponseError -> "No communication with the instrument").
_TRANSIENT_EXCEPTIONS = tuple(
    exc for exc in (
        getattr(minimalmodbus, "MasterReportedException", None),
        getattr(minimalmodbus, "NoResponseError", None),
        getattr(minimalmodbus, "InvalidResponseError", None),
        getattr(minimalmodbus, "LocalEchoError", None),
        serial.SerialException,
    )
    if exc is not None
)

class SerialCom(ModbusCom):
    def __init__(self, config_file: str):
        self.lock = threading.Lock()
        try:
            with open(config_file) as f:
                config = json.load(f)["serial"]
                self.port = config["port"]
                self.baudrate = config["baudrate"]
                self.bytesize = config["bytesize"]
                self.parity = getattr(serial, config["parity"])
                self.stopbits = config["stopbits"]
                self.timeout = config["timeout"]
                self.mode = getattr(minimalmodbus, config["mode"])
                self.clear_buffers_before_each_transaction = config["clear_buffers_before_each_transaction"]
                self.close_port_after_each_call = config["close_port_after_each_call"]
                # Retry tuning (optional, with safe defaults). Retrying transient
                # frame faults in-place recovers the reading within the same cycle
                # instead of wasting it on a single corrupted/truncated frame.
                self.retries = int(config.get("retries", 3))
                self.retry_backoff = float(config.get("retry_backoff", 0.01))
                # USB-serial (e.g. /dev/ttyACM*) defaults to a high latency timer
                # that dominates per-transaction time. Enabling low-latency mode
                # cuts the round-trip overhead without touching the baud rate.
                self.low_latency = bool(config.get("low_latency", True))
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            logging.error(f"Error loading configuration: {e}", exc_info=True)
            raise

        self.comport = minimalmodbus.Instrument(self.port, 1)  # Default address, will be changed in methods
        self.comport.serial.baudrate = self.baudrate
        self.comport.serial.bytesize = self.bytesize
        self.comport.serial.parity = self.parity
        self.comport.serial.stopbits = self.stopbits
        self.comport.serial.timeout = self.timeout
        self.comport.mode = self.mode
        self.comport.clear_buffers_before_each_transaction = self.clear_buffers_before_each_transaction
        self.comport.close_port_after_each_call = self.close_port_after_each_call

        os.makedirs("logs", exist_ok=True)
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler("logs/serial_com.log", maxBytes=1_000_000, backupCount=5),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.low_latency:
            self._enable_low_latency()

    def _enable_low_latency(self):
        """Enable the serial port's low-latency mode (cuts USB-serial round-trip).

        Best-effort: not all platforms/drivers support it, so any failure is
        logged and ignored rather than blocking startup. Has no effect on the
        baud rate or framing.
        """
        try:
            self.comport.serial.set_low_latency_mode(True)
            self.logger.info(f"Enabled low-latency mode on {self.port}")
        except (ValueError, NotImplementedError, OSError, AttributeError) as e:
            self.logger.warning(f"Could not enable low-latency mode on {self.port}: {e}")

    def _execute_with_lock(self, address: int, func, *args, **kwargs):
        """Execute a Modbus operation under the bus lock, retrying transient faults.

        Transient bus faults (corrupted/truncated frames, missing replies) are
        retried up to ``self.retries`` times with a short backoff, all while
        holding the lock so no other transaction can interleave. This recovers
        the reading within the current cycle instead of surfacing a single
        glitch as a hard failure. Non-transient errors are raised immediately.
        """
        with self.lock:
            self.logger.debug(f"Acquiring lock and setting address to {address}")
            self.comport.address = address
            attempts = max(1, self.retries + 1)
            last_exc = None
            for attempt in range(1, attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        self.logger.info(
                            f"Operation succeeded for address {address} on attempt {attempt}/{attempts}"
                        )
                    else:
                        self.logger.debug(f"Operation successful for address {address}")
                    return result
                except _TRANSIENT_EXCEPTIONS as e:
                    last_exc = e
                    self.logger.warning(
                        f"Transient error for address {address} "
                        f"(attempt {attempt}/{attempts}): {e}"
                    )
                    # A serial-layer failure can leave the port in a bad state;
                    # drop it so the next attempt/call transparently reopens it.
                    if isinstance(e, serial.SerialException):
                        self._reset_port()
                    if attempt < attempts:
                        time.sleep(self.retry_backoff * attempt)
                except Exception as e:
                    self.logger.warning(
                        f"Non-retryable error during operation at address {address}: {e}",
                        exc_info=True,
                    )
                    raise
                finally:
                    self.logger.debug(f"Releasing lock for address {address}")
            # Exhausted all retries on a transient fault.
            raise last_exc

    def _reset_port(self):
        """Close the underlying serial port so it is transparently reopened."""
        try:
            if self.comport.serial.is_open:
                self.comport.serial.close()
        except Exception as e:
            self.logger.warning(f"Failed to reset serial port: {e}")

    def read_float(self, address: int, register: int, number_of_registers: int):
        """Read float value from registers."""
        return self._execute_with_lock(address, self.comport.read_float, register, number_of_registers)

    def read_int(self, address: int, register: int, number_of_registers: int):
        """Read integer value from registers."""
        return self._execute_with_lock(address, self.comport.read_int, register, number_of_registers)

    def read_string(self, address: int, register: int, number_of_registers: int):
        """Read string value from registers."""
        return self._execute_with_lock(address, self.comport.read_string, register, number_of_registers)

    def write_float(self, address: int, register: int, value: float, number_of_decimals: int = 0):
        """Write float value to registers."""
        return self._execute_with_lock(address, self.comport.write_float, register, value, number_of_decimals)

    def write_int(self, address: int, register: int, value: int):
        """Write integer value to register."""
        return self._execute_with_lock(address, self.comport.write_int, register, value)

    def write_string(self, address: int, register: int, value: str):
        """Write string value to registers."""
        return self._execute_with_lock(address, self.comport.write_string, register, value)

    def read_register(self, address: int, register: int, number_of_registers: int, functioncode: int = 1):
        """Read registers using specified function code."""
        return self._execute_with_lock(address, self.comport.read_register, register, number_of_registers, functioncode)

    def write_register(
        self, 
        address: int, 
        registeraddress: int, 
        value: Union[int, float], 
        number_of_decimals: int = 0, 
        functioncode: int = 16, 
        signed: bool = False
    ) -> None:
        """
        Writes a value to a specified register.

        :param address: The address of the device to communicate with.
        :param registeraddress: The address of the register to write to.
        :param value: The value to write. Can be an integer or a float.
        :param number_of_decimals: Number of decimals for scaling the value (default is 0).
        :param functioncode: Modbus function code to use (default is 16).
        :param signed: Whether the value is signed (default is False).
        """
        def write_func():
            if number_of_decimals > 0:
                self.comport.write_register(
                    registeraddress, 
                    value, 
                    number_of_decimals=number_of_decimals, 
                    functioncode=functioncode, 
                    signed=signed
                )
            else:
                self.comport.write_register(
                    registeraddress, 
                    int(value), 
                    number_of_decimals=number_of_decimals, 
                    functioncode=functioncode, 
                    signed=signed
                )
            self.logger.info(f"Successfully wrote value {value} to register {registeraddress} at address {address}.")
        
        self._execute_with_lock(address, write_func)

    def read_block(self, address: int, register: int, number_of_registers: int):
        """Read a block of registers."""
        return self._execute_with_lock(address, self.comport.read_block, register, number_of_registers)

    def close(self):
        """Close the communication connection."""
        self.comport.serial.close()
        
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()