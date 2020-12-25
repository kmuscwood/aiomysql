"""Bit support"""


class Bit:
    """represent value from bit column"""

    def __init__(self, length):
        self.length = length
        self.value = None

    def as_binary(self):
        """convert to string of ones and zeros"""
        return f'{self.value:>b}'

    def __call__(self, value):
        if value is None:
            raise ValueError('None is not a bit value')
        if isinstance(value, int):
            self.value = value
            return self
        if isinstance(value, bytes):
            self.value = int.from_bytes(value, 'big')
            return self
        if not isinstance(value, str):
            raise ValueError(f"'{value}' is not a binary string")
        if set(b for b in value) not in (set('0'), set('1'), set(('0', '1'))):
            raise TypeError(f"'{value}' contains invalid bits")
        if len(value) > self.length:
            raise ValueError(f"'{value}' is too long (length={self.length})")
        self.value = int(value, 2)
        return self
