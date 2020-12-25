"""serialize/deserialize values between python and mysql"""
import datetime
import decimal
import json

from aiomysql.bit import Bit
from aiomysql.constants import FIELD_TYPE


def bytes_to_int(value):
    """cast byte value to int"""
    return int.from_bytes(value, 'big')


def quote(val):
    """quote val"""
    return f"'{val}'"


def from_float(val):
    """escape a python float"""
    return quote('%.15g' % val)


def from_bool(val):
    """escape a python bool"""
    return quote(int(val))


def from_string(val):
    """escape a python string"""
    escape = val.translate(
        str.maketrans({
            "'": "''",
            '\\': '\\\\',
            '\0': '\\0',
            '\b': '\\b',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            # ctrl z: windows end-of-file; escaped z deprecated in python
            '\x1a': '\\x1a',
        }))
    return f"'{escape}'"


def from_bytes(val):
    """escape a python byte array"""
    return from_string(val.decode('ascii', 'surrogateescape'))


def from_bit(val):
    """escape a aiodb.connector.mysql.Bit"""
    return f"b'{val.as_binary()}'"


def from_set(val):
    """escape a python set"""
    return from_string(','.join([str(item) for item in val]))


def from_date(val):
    """escape a python datetime.date"""
    return val.strftime("'%Y-%m-%d'")


def from_datetime(val):
    """escape a python datetime.datetime"""
    return val.strftime("'%Y-%m-%d %H:%M:%S.%f'")


def _time(hour, minute, second, microsecond):
    if microsecond:
        return f"'{hour:02d}:{minute:02d}:{second:02d}.{microsecond:06d}'"
    return f"'{hour:02d}:{minute:02d}:{second:02d}'"


def from_timedelta(val):
    """escape a python datetime.timedelta"""
    sec = int(val.total_seconds())
    hour = sec // 3600
    sec = sec % 3600
    mns = sec // 60
    sec = sec % 60
    msec = val.microseconds
    return _time(hour, mns, sec, msec)


def from_time(val):
    """escape a python datetime.time"""
    return _time(val.hour, val.minute, val.second, val.microsecond)


def to_datetime(value):
    """cast string value to datetime.datetime"""
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        pass
    return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


def to_date(value):
    """parse date value"""
    return datetime.datetime.strptime(value, '%Y-%m-%d').date()


def to_time(value):
    """cast time string to datetime.timedelta"""
    value = str(value)
    try:
        time, partial = value.split('.')
        microseconds = int((partial + '0000000')[:6])
    except ValueError:
        time = value
        microseconds = 0
    hours, minutes, seconds = (int(t) for t in time.split(':'))
    if hours <= 24:
        return datetime.time(hours, minutes, seconds, microseconds)
    return datetime.timedelta(hours=hours, minutes=minutes,
                              seconds=seconds, microseconds=microseconds)


from_mysql = {
    FIELD_TYPE.DECIMAL: decimal.Decimal,
    FIELD_TYPE.TINY: int,
    FIELD_TYPE.SHORT: int,
    FIELD_TYPE.INT24: int,
    FIELD_TYPE.LONG: int,
    FIELD_TYPE.LONGLONG: int,
    FIELD_TYPE.FLOAT: float,
    FIELD_TYPE.DOUBLE: float,
    FIELD_TYPE.TIMESTAMP: to_datetime,
    FIELD_TYPE.DATE: to_date,
    FIELD_TYPE.TIME: to_time,
    FIELD_TYPE.DATETIME: to_datetime,
    FIELD_TYPE.YEAR: int,
    FIELD_TYPE.JSON: json.loads,
    FIELD_TYPE.NEWDECIMAL: decimal.Decimal,
    FIELD_TYPE.BIT: bytes_to_int,
}


def to_mysql(val):
    """prepare val for use in sql statement"""
    if val is None:
        return 'NULL'

    return {
        bool: from_bool,
        int: quote,
        float: from_float,
        str: from_string,
        bytes: from_bytes,
        datetime.date: from_date,
        datetime.datetime: from_datetime,
        datetime.timedelta: from_timedelta,
        datetime.time: from_time,
        # time.struct_time: escape_struct_time,
        decimal.Decimal: quote,
        set: from_set,
        Bit: from_bit
    }[type(val)](val)
