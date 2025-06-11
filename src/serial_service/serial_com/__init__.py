"""
Modbus communication interfaces and implementations.

This module provides an abstract base class for Modbus communication
and concrete implementations for different transport methods.
"""

from .modbus_com import ModbusCom
from .serial_com import SerialCom
from .tcp_modbus import ModbusTcpCom

__all__ = ['ModbusCom', 'SerialCom', 'ModbusTcpCom'] 