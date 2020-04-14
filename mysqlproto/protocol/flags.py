from enum import Enum


class Capability(Enum):
    LONG_PASSWORD                  = 0x00000001
    FOUND_ROWS                     = 0x00000002
    LONG_FLAG                      = 0x00000004
    CONNECT_WITH_DB                = 0x00000008
    NO_SCHEMA                      = 0x00000010
    PROTOCOL_41                    = 0x00000200
    TRANSACTIONS                   = 0x00002000
    SECURE_CONNECTION              = 0x00008000
    PLUGIN_AUTH                    = 0x00080000
    CONNECT_ATTRS                  = 0x00100000
    PLUGIN_AUTH_LENENC_CLIENT_DATA = 0x00200000
    SESSION_TRACK                  = 0x00800000
    DEPRECATE_EOF                  = 0x01000000


class Status(Enum):
    STATUS_IN_TRANS             = 0x0001
    STATUS_AUTOCOMMIT           = 0x0002
    MORE_RESULTS_EXISTS         = 0x0008
    STATUS_NO_GOOD_INDEX_USED   = 0x0010
    STATUS_NO_INDEX_USED        = 0x0020
    STATUS_CURSOR_EXISTS        = 0x0040
    STATUS_LAST_ROW_SENT        = 0x0080
    STATUS_DB_DROPPED           = 0x0100
    STATUS_NO_BACKSLASH_ESCAPES = 0x0200
    STATUS_METADATA_CHANGED     = 0x0400
    QUERY_WAS_SLOW              = 0x0800
    PS_OUT_PARAMS               = 0x1000
    STATUS_IN_TRANS_READONLY    = 0x2000
    SESSION_STATE_CHANGED       = 0x4000

#https://dev.mysql.com/doc/internals/en/character-set.html#packet-Protocol::CharacterSet
class CharacterSet(Enum):
    utf8   = 0x21
    latin1_swedish_ci    = 0x08
    binary = 0x3f


class _EnumSet(set):
    __slots__ = ()

    @property
    def int(self):
        ret = 0
        for i in self:
            ret |= i.value
        return ret

    @int.setter
    def int(self, data):
        self.clear()
        for i in Capability:
            if i.value & data:
                self.add(i)


class CapabilitySet(_EnumSet):
    __slots__ = ()


class StatusSet(_EnumSet):
    __slots__ = ()
    enum = Status
