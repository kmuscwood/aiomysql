"""test serializer operation"""
import datetime
import pytest

import aiomysql.serializer as serializer


@pytest.mark.parametrize(
    'value,expected', (
        # normal
        ('a', "'a'"),
        # quotes
        ("'a", "'''a'"),
        ('"a', "'\"a'"),
        # backslash
        (r'\a', r"'\\a'"),
        # null
        ('a\0b', r"'a\0b'"),
        # backspace
        ('a\bb', r"'a\bb'"),
        # newline
        ('a\bb', r"'a\bb'"),
        # carriage return
        ('a\rb', r"'a\rb'"),
        # tab
        ('a\tb', r"'a\tb'"),
        # ctrl-z
        (chr(26), r"'\x1a'"),
        # combined
        ((' "abc"\r\n, \t\x00123'), ("' \"abc\"\\r\\n, \\t\\0123'")),
    ),
)
def test_string(value, expected):
    """test from_string"""
    assert serializer.from_string(value) == expected


@pytest.mark.parametrize(
    'value,expected', (
        (set(('a', 'b')), ("'a,b'", "'b,a'")),
        (set((1, 'b')), ("'1,b'", "'b,1'")),
        (set((1, 2)), ("'1,2'", "'2,1'")),
    ),
)
def test_from_set(value, expected):
    """test from_set"""
    assert serializer.from_set(value) in expected
