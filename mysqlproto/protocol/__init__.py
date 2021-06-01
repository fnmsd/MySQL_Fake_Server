import asyncio
import struct
import ssl

class _MysqlStreamSequence:
    __slots__ = '_seq'

    def __init__(self):
        self._seq = 0
    def get_seq(self):
        return self._seq
        
    def check(self, seq):
        # if seq != self._seq:
        #     raise RuntimeError('Wrong sequence, expected {}, got {}'.format(self._seq, seq))
        return self.incr()

    def incr(self):
        seq = self._seq
        self._seq = (seq + 1) & 0xff
        return seq

    def reset(self):
        self._seq = 0


class MysqlPacketReader:
    __slots__ = '_stream', '_seq', '__length', '__follow'

    def __init__(self, stream, seq):
        self._stream = stream
        self._seq = seq
        self.__length = 0
        self.__follow = True

    def get_seq(self):
        return self._seq.get_seq()
    def _check_lead(self, ldata):
        if not ldata or len(ldata) != 4:
            raise RuntimeError

        l1, l2, seq = struct.unpack("<HBB", ldata)
        l = l1 + (l2 << 16)

        self._seq.check(seq)

        self.__length = l
        if l < 0xffffff:
            self.__follow = False

    @asyncio.coroutine
    def close(self):
        while (yield from self.read()):
            pass

    @asyncio.coroutine
    def read(self, size=None):
        if not self.__length:
            if self.__follow:
                ldata = yield from self._stream.read(4)
                self._check_lead(ldata)
            else:
                return ''

        if not size or size >= self.__length:
            size = self.__length

        data = yield from self._stream.read(size)
        self.__length -= len(data)
        return data


class MysqlStreamReader:
    __slots__ = '_inner', '_seq'

    def __init__(self, inner, seq):
        self._inner = inner
        self._seq = seq

    def packet(self):
        return MysqlPacketReader(self._inner, self._seq)


class MysqlStreamWriter:
    __slots__ = '_inner', '_seq'

    def __init__(self, inner, seq):
        self._inner = inner
        self._seq = seq

    def close(self):
        self._inner.close()

    @asyncio.coroutine
    def drain(self):
        return self._inner.drain()

    def reset(self):
        self._seq.reset()

    def write(self, data):
        l = len(data)
        if l >= 0xffff:
            raise NotImplementedError

        ldata = struct.pack("<HBB", l, 0, self._seq.incr())
        #print(ldata+data)
        self._inner.write(ldata + data)
    def get_extra_info(self,key):
        return self._inner.get_extra_info(key)


@asyncio.coroutine
def start_mysql_server(client_connected_cb, host=None, port=None, **kwds):
    @asyncio.coroutine
    def cb(reader, writer):
        seq = _MysqlStreamSequence()
        reader_m = MysqlStreamReader(reader, seq)
        writer_m = MysqlStreamWriter(writer, seq)
        return client_connected_cb(reader_m, writer_m)
    # ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    # ssl_context.load_verify_locations('pymotw.crt')

    # ssl_context.check_hostname = False
    # #ssl_context.load_cert_chain('pymotw.crt', 'pymotw.key')
    return asyncio.start_server(cb, host, port, **kwds)
