import asyncio

import click

from aiomysql.connection import MysqlConnection


@click.command()
@click.argument("host")
@click.argument("user")
@click.option("--password", default="")
@click.option("--database")
@click.argument("query")
def select(host, user, password, database, query):
    """simple query runner"""

    async def _select():
        con = await MysqlConnection.connect(host, user, password, database)
        cols, rows = await con.execute(query)
        for row in rows:
            print(dict(zip(cols, row)))

    asyncio.run(_select())


if __name__ == "__main__":
    select()
