"""mysql packet handling routines"""
import struct

import aiomysql.charset as charset
from aiomysql.constants import CLIENT, SERVER_STATUS, CAPABILITIES
from aiomysql.password import scramble


MAX_PACKET_LEN = 2**24-1

NULL_COLUMN = 251
UNSIGNED_CHAR_COLUMN = 251
UNSIGNED_SHORT_COLUMN = 252
UNSIGNED_INT24_COLUMN = 253
UNSIGNED_INT64_COLUMN = 254


def serialize(payload, sequence):
    """serialize data for transport to mysql"""
    length = struct.pack('<I', len(payload))[:3]
    sequence = struct.pack("!B", sequence)
    return length + sequence + payload


class Packet:
    """generic packet"""

    def __init__(self, data):
        self.data = data
        self.position = 0

    def read(self, size):
        """read 'size' bytes from data"""
        result = self.data[self.position:self.position+size]
        self.position += size
        return result

    def read_all(self):
        """read remainder from data"""
        result = self.data[self.position:]
        self.position = None  # ensure no subsequent read()
        return result

    def read_uint8(self):
        """read uint8 from data"""
        result = self.data[self.position]
        self.position += 1
        return result

    def read_uint16(self):
        """read uint16 from data"""
        result = struct.unpack_from('<H', self.data, self.position)[0]
        self.position += 2
        return result

    def read_uint24(self):
        """read uint24 from data"""
        low, high = struct.unpack_from('<HB', self.data, self.position)
        self.position += 3
        return low + (high << 16)

    def read_uint32(self):
        """read uint32 from data"""
        result = struct.unpack_from('<I', self.data, self.position)[0]
        self.position += 4
        return result

    def read_uint64(self):
        """read uint64 from data"""
        result = struct.unpack_from('<Q', self.data, self.position)[0]
        self.position += 8
        return result

    def read_string(self):
        """read a string from data"""
        end_pos = self.data.find(b'\0', self.position)
        if end_pos < 0:
            return None
        result = self.data[self.position:end_pos]
        self.position = end_pos + 1
        return result

    def read_length_encoded_integer(self):
        """Read a 'Length Coded Binary' number from the data buffer.

        Length coded numbers can be anywhere from 1 to 9 bytes depending
        on the value of the first byte.
        """
        num = self.read_uint8()
        if num == NULL_COLUMN:
            return None
        if num < UNSIGNED_CHAR_COLUMN:
            return num
        if num == UNSIGNED_SHORT_COLUMN:
            return self.read_uint16()
        if num == UNSIGNED_INT24_COLUMN:
            return self.read_uint24()
        if num == UNSIGNED_INT64_COLUMN:
            return self.read_uint64()
        return None

    def read_length_coded_string(self):
        """Read a 'Length Coded String' from the data buffer.

        A 'Length Coded String' consists first of a length coded
        (unsigned, positive) integer represented in 1-9 bytes followed by
        that many bytes of binary data.  (For example "cat" would be "3cat".)
        """
        length = self.read_length_encoded_integer()
        if length is None:
            return None
        return self.read(length)


class Handshake(Packet):  # pylint: disable=too-many-instance-attributes
    """mysql handshake packet"""

    def __init__(self, data):
        # https://dev.mysql.com/doc/internals/en/connection-phase-packets.html#packet-Protocol::Handshake
        super().__init__(data)

        self.server_language = 0
        self.server_charset = None
        self.server_status = 0
        self.auth_plugin_name = None

        self.protocol_version = self.read_uint8()

        self.server_version = self.read_string()

        self.connection_id = self.read_uint32()

        self.salt = self.read(8)
        self.read(1)  # filler

        self.server_capabilities = self.read_uint16()

        if len(data) >= self.position + 6:
            self.server_language = self.read_uint8()
            self.server_status = self.read_uint16()
            cap_h = self.read_uint16()
            salt_len = self.read_uint8()

            self.server_charset = \
                charset.charset_by_id(self.server_language).name
            self.server_capabilities |= cap_h << 16
            salt_len = max(12, salt_len - 9)

        # reserved
        self.read(10)

        if len(data) >= self.position + salt_len:
            # salt_len includes auth_plugin_data_part_1 and filler
            self.salt += self.read(salt_len)

        self.read(1)
        if self.server_capabilities & CAPABILITIES.CLIENT_PLUGIN_AUTH \
                and len(data) >= self.position:
            self.auth_plugin_name = self.read_string().decode('latin1')

    def __repr__(self):
        return (
            f"Handshake[protocol={self.protocol_version}"
            f", version={self.server_version}"
            f", connection={self.connection_id}"
            f", salt={self.salt}"
            f", capabilities={self.server_capabilities}"
            f", language={self.server_language}"
            f", charset={self.server_charset}"
            f", status={self.server_status}"
            f", plugin={self.auth_plugin_name}" f"]"
        )

    @property
    def autocommit(self):
        """indicate autocommit setting"""
        return bool(self.server_status & SERVER_STATUS.AUTOCOMMIT)


def handshake_response(handshake, user, password, database=None):
    """create response to handshake success"""
    charset_id = charset.charset_by_name('utf8').id
    encoding = charset.charset_by_name('utf8').encoding

    data = struct.pack('<iIB23s', CLIENT.CAPABILITIES, 1, charset_id, b'')
    data = data + user.encode(encoding) + b'\0'

    authresp = b''
    if handshake.auth_plugin_name in ('', 'mysql_native_password'):
        authresp = scramble(password.encode('latin1'), handshake.salt)

    data += struct.pack('B', len(authresp)) + authresp

    if handshake.server_capabilities & CLIENT.CONNECT_WITH_DB:
        if database:
            data += database.encode(encoding)
        data += b'\0'

    name = handshake.auth_plugin_name
    data += name.encode('ascii') + b'\0'

    return data


def generic(data):
    """handle generic data arrival"""
    if is_ok(data):
        return OK(data)
    if is_eof(data):
        if len(data) < 9:
            return EOF(data)
        return OK(data)
    if is_error(data):
        return ERR(data)
    raise Exception(f"unexpected packet header '{data}'")


def row_data(data):
    """handle tuple (row) data arrival"""
    if is_ok(data):
        return OK(data)
    if is_eof(data):
        if len(data) < 9:
            return EOF(data)
        return OK(data)
    return Packet(data)


def query_response(data):
    """return packet from data containing query response"""
    if is_ok(data):
        return OK(data)
    if is_error(data):
        return ERR(data)
    return FIELD_LENGTH(data)


def is_ok(data):
    """check for ok indication in data"""
    return data[0] == 0


def is_eof(data):
    """check for eof indication in data"""
    return data[0] == 254


def is_error(data):
    """check for error indication in data"""
    return data[0] == 255


class FIELD_LENGTH(Packet):  # pylint: disable=invalid-name
    """mysql field length packet"""

    def __init__(self, data):
        super().__init__(data)
        self.type = 'field_length'
        self.field_length = self.read_length_encoded_integer()

    def __repr__(self):
        return (
            "FIELD_LENGTH["
            f"field_length={self.field_length}"
            ']'
        )


class OK(Packet):
    """mysql ok packet"""

    def __init__(self, data):
        super().__init__(data)
        self.type = 'ok'
        self.read_uint8()
        self.affected_rows = self.read_length_encoded_integer()
        self.last_insert_id = self.read_length_encoded_integer()
        self.status_flags = self.read_uint16()
        self.warnings = self.read_uint16()
        self.message = self.read_all()

    @property
    def has_next(self):
        """return True if packet indicates more results coming"""
        return self.status_flags & SERVER_STATUS.SERVER_MORE_RESULTS_EXISTS

    def __repr__(self):
        return (
            "OK["
            f"affected_rows={self.affected_rows}"
            f", last_insert_id={self.last_insert_id}"
            f", status_flags={self.status_flags}"
            f", warnings={self.warnings}"
            f", has_next={self.has_next}"
            f", message={self.message}"
            ']'
        )


class EOF(Packet):
    """mysql eof packet"""

    def __init__(self, data):
        super().__init__(data)
        self.type = 'eof'
        self.read_uint8()
        self.warnings = self.read_uint16()
        self.status_flags = self.read_uint16()

    def __repr__(self):
        return (
            "EOF["
            f"warnings={self.warnings}"
            f", status_flags={self.status_flags}"
            ']'
        )


class ERR(Packet):
    """mysql error packet"""

    def __init__(self, data):
        super().__init__(data)
        self.type = 'error'
        self.read_uint8()
        self.error_code = self.read_uint16()
        self.sql_state_marker = self.read(1)
        self.sql_state = self.read(5)
        self.error_message = self.read_all().decode()

    def __repr__(self):
        return (
            "ERR["
            f"error_code={self.error_code}"
            f", sql_state_marker={self.sql_state_marker}"
            f", sql_state={self.sql_state}"
            f", error_message={self.error_message}"
            ']'
        )


class ColumnDefinition(Packet):  # pylint: disable=too-many-instance-attributes
    """mysql column definition packet"""

    def __init__(self, data):
        super().__init__(data)
        self.type = 'column_definition'
        self.catalog = self.read_length_coded_string()
        self.schema = self.read_length_coded_string()
        self.table = self.read_length_coded_string()
        self.org_table = self.read_length_coded_string()
        self.name = self.read_length_coded_string()
        self.org_name = self.read_length_coded_string()

        header = struct.Struct('<xHIBHBxx')
        self.character_set, self.length, self.type, self.flags, \
            self.decimals = header.unpack_from(self.data, self.position)
        self.position += header.size

    def __repr__(self):
        return (
            "ColumnDefinition["
            f"catalog={self.catalog}"
            f", schema={self.schema}"
            f", table={self.table}"
            f", org_table={self.org_table}"
            f", name={self.name}"
            f", org_name={self.org_name}"
            f", character_set={self.character_set}"
            f", length={self.length}"
            f", type={self.type}"
            f", flags={self.flags}"
            f", decimals={self.decimals}"
            ']'
        )
