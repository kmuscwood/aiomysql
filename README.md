# aiomysql

### asyncio enabled mysql connection

If you are creating program using `asyncio`
and want to interact with `mysql` in a non-blocking
way, this code might be useful to you.

**Note**: This is very basic connect + execute
functionality.
No pooling or ORM support is provided,
although these features could be layered
on top of this code.

### Interface

### `aiomysql.connection.MysqlConnection`

#### `async connect(host, user, password="", database="", port=3306, autocommit=False, isolation=None): MysqlConnection`

The `connect` classmethod returns a `MysqlConnection` instance that is connected to a `mysql` database.
The connection remains open until the `close` method is called, or until it is closed by the `mysql` server.

* host       - hostname or IP address of mysql server
* user       - mysql user
* password   - password for mysql user
* database   - name of database
* port       - mysql listening port
* autocommit - autocommit for connection (else per mysql)
* isolation  - isolation level for connection (else per mysql)
               (eg: "REPEATABLE READ", "READ UNCOMMITED" ...)

**raises** `aiomysql.connection.AuthenticationError` if unable to authenticate

#### `async execute(query): [column_name, ...] [[value, ...], ...]`

The `execute` method runs a command (`query`) and returns a list of column names and a list of rows.
On non-`QUERY` commands, both lists are empty.

If the `query` is an `INSERT` command and results in an `AUTOINCREMENT` column being set, use the `last_id` method to obtain this value after executing the `query`.

Use the `last_message` method to obtain the message associated with the latest `execute` call.

**raises** `aiomysql.connection.CommandException` if the `mysql` server returns an error

**Note**: It is expected that the `query` argument has been properly escaped to prevent SQL injection attacks. See the `serialize` classmethod.

#### `async close()`

Close the connection.

#### `last_id()`

Return the `AUTOINCREMENT` key (if any) generated from the most recent `INSERT`.
This value is reset after each call to `execute`.

#### `last_message()`

Return the message generated from the most recent `execute`.

#### `serialize(value)`

The `serialize` classmethod serializes and escapes a value for safe
use in a SQL statement.

##### examples

```
>>> insert = "INSERT INTO table (field) VALUES (%s)"
>>> value = MysqlConnection.serialize(";DELETE FROM users")
>>> insert % value
"INSERT INTO table (field) VALUES (';DELETE FROM users')"
```

```
MysqlConnction.serialize(datetime.now())
"'2020-01-01 22:33:44.776827'"
```

##### supported types

The following types are serialized:

```
bool
int
float
str
bytes
datetime.date
datetime.datetime
datetime.timedelta
datetime.time
decimal.Decimal
set
```

In addition, `None` is serialized as `NULL`, and
special handling for `BIT` columns are supported with
`aiomysql.bit.Bit`.
