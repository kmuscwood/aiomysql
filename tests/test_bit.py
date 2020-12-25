"""test Bit operations"""
import pytest

from aiomysql.bit import Bit


@pytest.mark.parametrize(
    'length, value, expected', (
        (10, None, ValueError),
        (10, 1, 1),
        (10, '123', TypeError),
        (10, '0', 0),
        (10, '1', 1),
        (10, '010', 2),
        (10, '1010', 10),
        (10, '01000000000', ValueError),
    ),
)
def test_bit(length, value, expected):
    """test different inputs"""
    bit = Bit(length)
    if expected in (ValueError, TypeError):
        with pytest.raises(expected):
            bit(value)
    else:
        assert bit(value).value == expected


def test_as_binary():
    """verify binary conversion"""
    bit = Bit(5)(10)
    assert bit.as_binary() == '1010'
