"""password utilities"""
from functools import partial
import hashlib
import struct


def scramble(password, message):
    """scramble message with password"""
    scramble_length = 20
    sha_new = partial(hashlib.new, 'sha1')

    if not password:
        return b''
    stage1 = sha_new(password).digest()
    stage2 = sha_new(stage1).digest()
    buf = sha_new()
    buf.update(message[:scramble_length])
    buf.update(stage2)
    result = buf.digest()
    return _crypt(result, stage1)


def _crypt(message1, message2):
    length = len(message1)
    result = b''
    for i in range(length):
        buf = (struct.unpack('B', message1[i:i+1])[0] ^
               struct.unpack('B', message2[i:i+1])[0])
        result += struct.pack('B', buf)
    return result
