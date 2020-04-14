import asyncio
import struct

from .flags import Capability, CapabilitySet, Status, StatusSet, CharacterSet


class HandshakeV10:
    def __init__(self):
        self.server_version = '5.0.2'

        self.capability = CapabilitySet((
            Capability.LONG_PASSWORD,
            Capability.LONG_FLAG,
            Capability.CONNECT_WITH_DB,
            Capability.PROTOCOL_41,
            Capability.TRANSACTIONS,
            Capability.SECURE_CONNECTION,
            Capability.PLUGIN_AUTH,
        ))
        self.status = StatusSet((
            Status.STATUS_AUTOCOMMIT,
        ))
        self.character_set = CharacterSet.utf8

        self.auth_plugin = 'mysql_clear_password'

    def write(self, stream):
        capability = struct.pack('<I', self.capability.int)
        status = struct.pack('<H', self.status.int)

        packet = [
            b'\x0a',
            self.server_version.encode('ascii'), b'\x00',
            b'\x00'*4,
            b'\x01'*8,
            b'\x00',
            capability[:2],
            bytes((self.character_set.value, )),
            status,
            capability[2:],
            b'\x00',
            b'\x01'*10,
        ]

        if Capability.SECURE_CONNECTION in self.capability:
            packet.append(b'\x00'*13)

        if Capability.PLUGIN_AUTH in self.capability:
            packet.extend((self.auth_plugin.encode('ascii'), b'\x00'))

        p = b''.join(packet)
        stream.write(p)


class HandshakeResponse41:
    _packet_1 = struct.Struct('<IIB23x')

    def __init__(self):
        self.capability = CapabilitySet()

    @classmethod
    @asyncio.coroutine
    def read(cls, packet, capability_announced):
        data = yield from packet.read()

        ret = cls()

        d = cls._packet_1.unpack(data[:cls._packet_1.size])
        ret.capability.int = d[0]
        ret.capability_effective = ret.capability & capability_announced
        ret.max_packet_size = d[1]
        ret.character_set = CharacterSet(d[2])

        if not Capability.PROTOCOL_41 in ret.capability:
            raise RuntimeError

        cur = cls._packet_1.size
        end = data.index(b'\x00', cur)
        ret.user = data[cur:end]
        cur = end + 1

        if Capability.PLUGIN_AUTH_LENENC_CLIENT_DATA in ret.capability_effective:
            raise NotImplementedError
        elif Capability.SECURE_CONNECTION in ret.capability_effective:
            i = data[cur]
            end = cur + i + 1
            ret.auth_response = data[cur + 1:end]
            cur = end
        else:
            raise NotImplementedError

        if Capability.CONNECT_WITH_DB in ret.capability_effective:
            end = data.index(b'\x00', cur)
            ret.schema = data[cur:end].decode('ascii')
            cur = end + 1
        else:
            ret.schema = None

        if Capability.PLUGIN_AUTH in ret.capability_effective:
            end = data.index(b'\x00', cur)
            ret.auth_plugin = data[cur:end].decode('ascii')
            cur = end + 1

        if Capability.CONNECT_ATTRS in ret.capability_effective:
            raise NotImplementedError

        return ret


class AuthSwitchRequest:
    def __init__(self):
        self.auth_plugin = 'mysql_clear_password'

    def write(self, stream):
        packet = [
            b'\xfe',
            self.auth_plugin.encode('ascii'), b'\x00',
        ]

        p = b''.join(packet)
        stream.write(p)
