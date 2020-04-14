import struct


class IntLengthEncoded:
    _len_2 = struct.Struct('<cH')
    _len_3 = struct.Struct('<cHB')
    _len_8 = struct.Struct('<cQ')

    @classmethod
    def write(cls, data):
        if data < 0:
            raise ValueError
        elif data < 251:
            return bytes((data, ))
        elif data < 2**16:
            return cls._len_2.pack(b'\xfc', data)
        elif data < 2**24:
            return cls._len_3.pack(b'\xfd', data & 0xffff, data >> 16)
        elif data < 2**64:
            return cls._len_8.pack(b'\xfe', data)
        else:
            raise ValueError


class StringLengthEncoded:
    @staticmethod
    def write(data):
        l = IntLengthEncoded.write(len(data))
        return l + data

