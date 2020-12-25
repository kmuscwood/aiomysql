"""test operations with null"""
import asyncio

from aiomysql.connection import MysqlConnection


def test_null(connect_params):
    """verify null column comes back as None"""

    async def _test_null():
        con = await MysqlConnection().connect(**connect_params)
        insert = "INSERT INTO `test` (`a_dec`) VALUES (%s)"
        insert = insert % con.serialize(10)
        await con.execute(insert)
        select = "SELECT `id`, `a_dec`, `b_tin` FROM `test`"
        _, tuples = await con.execute(select)
        assert tuples[0][1] == 10
        assert tuples[0][2] is None
        await con.close()

    asyncio.run(_test_null())
