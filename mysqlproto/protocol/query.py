import asyncio
import struct

from .types import IntLengthEncoded, StringLengthEncoded

#https://dev.mysql.com/doc/internals/en/protocoltext-resultset.html
class ColumnDefinition:
    def __init__(self, name,col_type=b"\xfc"):
        self.name = name
        self.col_type = col_type

    def write(self, stream):
        packet = [
            StringLengthEncoded.write(b'def'),#catalog
            StringLengthEncoded.write(b''),#schema 
            StringLengthEncoded.write(b'a'),#table 
            StringLengthEncoded.write(b'a'),#org_table 
            StringLengthEncoded.write(self.name.encode('ascii')),
            StringLengthEncoded.write(self.name.encode('ascii')),
            b'\x0c' #filter1
            b'\x3f\x00', #character_set
            b'\x1c\x00\x00\x00', #column_length
            #b'\xfc', #column_type 
            self.col_type, #column_type 
            b'\xff\xff', #flags 
            b'\x00', #decimals
            b'\x00'*2, #filler_2 
        ]

        p = b''.join(packet)
        #print(p)
        stream.write(p)


class ColumnDefinitionList:
    def __init__(self, columns=None):
        self.columns = columns or []

    def write(self, stream):
        p = IntLengthEncoded.write(len(self.columns))

        stream.write(p)

        for i in self.columns:
            i.write(stream)

class FileReadPacket:
    def __init__(self, filename=None):
        self.filename = filename

    def write(self, stream):
        print("reading file:"+self.filename.decode("ascii"))
        # stream.write(p)
        # stream.write(b'\x00\x00\x01')
        stream.write(b'\xfb'+self.filename)

class ResultSet:
    def __init__(self, values):
        self.values = values

    def write(self, stream):
        s = StringLengthEncoded.write

        packet = []

        for i in self.values:
            if i is None:
                packet.append(b'\xfb')
            else:
                if isinstance(i,bytes):
                    packet.append(s(i))
                elif isinstance(i,int):
                    packet.append(IntLengthEncoded.write(i))
                else:
                    packet.append(s(str(i).encode('ascii')))
        p = b''.join(packet)
        stream.write(p)
