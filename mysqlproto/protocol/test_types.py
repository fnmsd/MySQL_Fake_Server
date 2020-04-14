import pytest

from .types import IntLengthEncoded, StringLengthEncoded

def test_IntLengthEncoded_write():
    w = IntLengthEncoded.write
    assert w(0)       == b'\x00'
    assert w(1)       == b'\x01'
    assert w(250)     == b'\xfa'
    assert w(251)     == b'\xfc\xfb\x00'
    assert w(2**16-1) == b'\xfc\xff\xff'
    assert w(2**16)   == b'\xfd\x00\x00\x01'
    assert w(2**24-1) == b'\xfd\xff\xff\xff'
    assert w(2**24)   == b'\xfe\x00\x00\x00\x01\x00\x00\x00\x00'
    assert w(2**64-1) == b'\xfe\xff\xff\xff\xff\xff\xff\xff\xff'
    with pytest.raises(ValueError):
        w(2**64)
    with pytest.raises(ValueError):
        w(-1)

def test_StringLengthEncoded_write():
    w = StringLengthEncoded.write
    assert w(b'')  == b'\x00'
    assert w(b'a') == b'\x01a'
