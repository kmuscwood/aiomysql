"""tests for various column types"""
import asyncio
import datetime
from decimal import Decimal

import pytest

from aiomysql.bit import Bit
from aiomysql.connection import MysqlConnection


async def _handle(connect_params, column, value, expect=None):
    con = await MysqlConnection().connect(**connect_params)
    insert = f"INSERT INTO `test` (`{column}`)VALUES(%s)"
    insert = insert % con.serialize(value)
    await con.execute(insert)

    select = f"SELECT `{column}` FROM `test`WHERE id=%s"
    select = select % con.serialize(con.last_id())
    _, tuples = await con.execute(select)
    item = tuples[0][0]  # first row, first column

    if expect is None:
        assert item == value
    else:
        assert item == expect

    await con.close()


@pytest.mark.parametrize(
    'column,value,expect', (
        # decimal
        ('a_dec', Decimal('123.456'), None),
        # tinyint
        ('b_tin', 100.1, 100),
        ('b_tin', -10, None),
        # smallint
        ('b_sma', '100', 100),
        ('b_sma', 100.1, 100),
        ('b_sma', -10, None),
        # mediumint
        ('b_med', 0, None),
        ('b_med', 10, None),
        ('b_med', 100.1, 100),
        ('b_med', -10, None),
        # int
        ('b_int', 0, None),
        ('b_int', 100.1, 100),
        ('b_int', -10, None),
        # bigint
        ('b_big', 0, None),  # bigint
        ('b_big', 10, None),
        ('b_big', 100.1, 100),
        ('b_big', -10, None),
        # float
        ('c_flo', -1, None),
        ('c_flo', 0.1, None),
        ('c_flo', -0.1, None),
        ('c_flo', 123.456, None),
        ('c_flo', '123.456', 123.456),
        # double
        ('d_dou', 0, None),
        ('d_dou', 1, None),
        ('d_dou', -1, None),
        ('d_dou', 0.1, None),
        ('d_dou', -0.1, None),
        ('d_dou', 123.456, None),
        ('d_dou', '123.456', 123.456),
        # bit
        ('e_bit', Bit(5)(10), 10),
        # datetime
        ('f_dtm', '2020-01-02', datetime.datetime(2020, 1, 2)),
        ('f_dtm', '2020-01-02 12:13:14',
         datetime.datetime(2020, 1, 2, 12, 13, 14)),
        ('f_dtf', datetime.datetime(2020, 1, 2, 12, 13, 14),
         None),  # datetime(6)
        ('f_dtf', datetime.datetime(2020, 1, 2, 12, 13, 14, 321), None),
        # timestamp(6)
        ('f_tms', '2020-01-02', datetime.datetime(2020, 1, 2)),
        ('f_tms', '2020-01-02 12:13:14',
         datetime.datetime(2020, 1, 2, 12, 13, 14)),
        ('f_tms', datetime.datetime(2020, 1, 2, 12, 13, 14), None),
        ('f_tms', datetime.datetime(2020, 1, 2, 12, 13, 14, 321), None),
        # date
        ('f_dat', '2020-01-02', datetime.date(2020, 1, 2)),
        ('f_dat', '2020-01-02 12:13:14', datetime.date(2020, 1, 2)),
        ('f_dat', datetime.date(2020, 1, 2), None),
        # time
        ('f_tim', '12:01:02', datetime.time(12, 1, 2)),
        ('f_tim', '50:01:02',
         datetime.timedelta(hours=50, minutes=1, seconds=2)),
        # year
        ('f_yea', '2020', 2020),
        ('f_yea', 2020, None),
        # char(10)
        ('g_cha', 'akk', None),
        ('g_cha', 'καλι', None),
        # varchar(100)
        ('g_vch', 'akk', None),
        ('g_vch', 'καλι', None),
        # binary(10)
        ('g_bin', 'akk', b'akk' + b'\x00' * 7),
        ('g_bin', 'καλι', ('καλι'.encode() + b'\x00' * 10)[:10]),
        ('g_bin', b'\x00akk', b'\x00akk' + b'\x00' * 6),
        # varbinary(10)
        ('g_vbi', 'akk', b'akk'),
        ('g_vbi', 'καλι', 'καλι'.encode()),
        ('g_vbi', b'\x00akk', None),
        # tinyblob
        ('g_tbl', 'akk', b'akk'),
        ('g_tbl', 'καλι', 'καλι'.encode()),
        ('g_tbl', b'\x00akk', None),
        # blob
        ('g_blo', 'akk', b'akk'),
        ('g_blo', 'καλι', 'καλι'.encode()),
        ('g_blo', b'\x00akk', None),
        # mediumblob
        ('g_mbl', 'akk', b'akk'),
        ('g_mbl', 'καλι', 'καλι'.encode()),
        ('g_mbl', b'\x00akk', None),
        # longblob
        ('g_lbl', 'akk', b'akk'),
        ('g_lbl', 'καλι', 'καλι'.encode()),
        ('g_lbl', b'\x00akk', None),
        # tinytext
        ('g_tte', 'akk', None),
        ('g_tte', 'καλι', None),
        ('g_tte', b'\x00akk', '\x00akk'),
        # text
        ('g_tex', 'akk', None),
        ('g_tex', 'καλι', None),
        ('g_tex', b'\x00akk', '\x00akk'),
        # longtext
        ('g_lte', 'akk', None),
        ('g_lte', 'καλι', None),
        ('g_lte', b'\x00akk', '\x00akk'),
        # enum
        ('g_enu', 'three', None),
        # set
        ('g_set', 'one,two', None),
        # json
        ('h_jso', '{"a": 1}', dict(a=1)),
        ('h_jso', '["a", 1]', ['a', 1]),

    )
)
def test_column(connect_params, column, value, expect):
    """test a value saved and selected from a column"""
    asyncio.run(_handle(connect_params, column, value, expect))
