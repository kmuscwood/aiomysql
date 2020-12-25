"""connection to mysql"""
import asyncio
import struct

import aiomysql.charset as charset
from aiomysql.constants import COMMAND, FIELD_TYPE
import aiomysql.serializer as serializer
from aiomysql import packet


class AuthenticationError(Exception):
    """unable to authenticate"""


class CommandException(Exception):
    """error running mysql command"""


class MysqlConnection:
    """manage a connection to a mysql database"""

    def __init__(self):
        self.reader = None
        self.writer = None
        self.sequence = 0
        self.handshake = None
        self.encoding = charset.charset_by_name("utf8").encoding
        self._last_id = None
        self._last_message = None

    async def connect(self,  # pylint: disable=too-many-arguments
                      host, user, password="", database="", port=3306,
                      autocommit=False, isolation=None):
        """connect and authenticate to mysql"""
        self.reader, self.writer = await asyncio.open_connection(host, port)
        self.handshake = await self.next_packet(packet.Handshake)
        self.send(packet.handshake_response(self.handshake, user, password,
                                            database))
        response = await self.next_packet()
        if isinstance(response, packet.ERR):
            raise AuthenticationError(response.error_message)

        if autocommit is not self.handshake.autocommit:
            await self.execute(f"SET AUTOCOMMIT = {1 if autocommit else 0}")

        if isolation is not None:
            await self.execute(
                f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation}")

        return self

    def serialize(self, value):
        """escape and serialize a value"""
        return serializer.to_mysql(value)

    async def execute(self,  # pylint: disable=unused-argument
                      query, **kwargs):
        """execute query, return [column names], [[row], ...]"""
        self.execute_command(COMMAND.COM_QUERY, query)
        response = await self.next_packet(packet.query_response)
        if isinstance(response, packet.ERR):
            raise CommandException(response.error_message)

        # --- empty result
        if isinstance(response, packet.OK):
            self._last_id = response.last_insert_id
            self._last_message = response.message.decode()
            return [], []

        # --- column definitions
        defns = []
        for _ in range(response.field_length):
            defn = await self.next_column_definition()
            defns.append(defn)
        _ = await self.next_packet()  # extra packet after defns

        # --- rows
        rows = []
        while True:
            pkt = await self.next_packet(packet.row_data)
            if isinstance(pkt, (packet.OK, packet.EOF)):
                break
            row = []
            for defn in defns:
                value = pkt.read_length_coded_string()
                if value is not None:
                    value = defn.convert(value)
                row.append(value)
            rows.append(row)

        return defns, rows

    def execute_command(self, command_type, sql):
        """send off sql command"""
        sql = sql.encode(self.encoding)
        sql = struct.pack('B', command_type) + sql
        self.sequence = 0
        while sql:
            packet_size = min(packet.MAX_PACKET_LEN, len(sql))
            self.send(sql[:packet_size])
            sql = sql[packet_size:]

    def send(self, payload):
        """send payload to mysql"""
        self.writer.write(packet.serialize(payload, self.sequence))
        self.sequence += 1

    def last_id(self):
        """return last autoincrement id"""
        return self._last_id

        return self._last_id

    def last_message(self):
        """return message from last OK packet"""
        return self._last_message

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def next_packet(self, packet_type=packet.generic):
        """read next packet from mysql"""
        header = await self.reader.read(4)
        low, high, packet_number = struct.unpack('<HBB', header)
        if packet_number != self.sequence:
            raise Exception(
                f"Packet sequence {packet_number} != {self.sequence}")
        self.sequence += 1
        length = low + (high << 16)
        data = await self.reader.read(length)
        return packet_type(data)

    async def next_column_definition(self):
        """read and set up next column definition"""
        defn = await self.next_packet(packet.ColumnDefinition)

        if defn.type == FIELD_TYPE.JSON:
            encoding = self.encoding
        elif defn.type in FIELD_TYPE.TEXT_TYPES:
            if defn.character_set == FIELD_TYPE.ENCODING_BINARY:
                encoding = None
            else:
                encoding = self.encoding
        else:
            encoding = "ascii"
        converter = serializer.from_mysql.get(defn.type)

        def convert(encoding, converter):
            def _convert(value):
                if encoding:
                    value = value.decode(encoding)
                if converter:
                    value = converter(value)
                return value
            return _convert

        defn.convert = convert(encoding, converter)
        return defn
