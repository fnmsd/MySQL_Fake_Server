import asyncio
import struct

from .flags import Capability, CapabilitySet, Status, StatusSet, CharacterSet


class OK:
    def __init__(self, capability, status, warnings=0, info=''):
        self.status = status
        self.warnings = warnings
        self.info = info

    def write(self, stream):
        status_warnings = struct.pack('<HH', self.status.int, self.warnings)

        packet = [
            b'\x00',
            b'\x00',
            b'\x00',
            status_warnings,
            self.info.encode('ascii'),
        ]

        p = b''.join(packet)
        stream.write(p)


class ERR:
    def __init__(self, capability, sql_state='HY000', error=1096, error_msg='Go away'):
        self.sql_state = sql_state
        self.error = error
        self.error_msg = error_msg

    def write(self, stream):
        error = struct.pack('<H1s5s', self.error, b'#', self.sql_state.encode('ascii'))

        packet = [
            b'\xff',
            error,
            self.error_msg.encode('ascii'),
        ]

        p = b''.join(packet)
        stream.write(p)


class EOF:
    def __init__(self, capability, status, warnings=0):
        self.status = status
        self.warnings = warnings

    def write(self, stream):
        status_warnings = struct.pack('<HH', self.warnings, self.status.int)

        packet = [
            b'\xfe',
            status_warnings,
        ]

        p = b''.join(packet)
        stream.write(p)
