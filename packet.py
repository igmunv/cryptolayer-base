from enum import Enum, auto, unique
import struct


class PackTypes(Enum):
    SERVICE = auto()
    COMMUNIC = auto()

class DataTypes(Enum):
    TEXT = auto()
    PHOTO = auto()
    BYTES = auto()

class CMDTypes(Enum):
    PING = auto()
    UPDATE_KEYS = auto()
    DISCONNECT = auto()
    MY_NODE_ID = auto()
    MY_SIGN = auto()
    MY_PUBLIC_KEY = auto()


class Packet:


    HEADER_FORMAT = "!BHBHH"
    TOTAL_SIZE = struct.calcsize(HEADER_FORMAT)

    size = None
    pack_type = None
    payload = None
    chunk_count = None
    stream_id = None
    chunk_id = None


    def __init__(self, pack_type, payload, chunk_count, stream_id, chunk_id):
        self.pack_type = pack_type
        self.chunk_count = chunk_count
        self.stream_id = stream_id
        self.chunk_id = chunk_id
        self.payload = payload
        self.size = len(payload)


    def to_bytes(self):
        # Динамически упаковывает payload любой длины
        dynamic_format = f"{self.HEADER_FORMAT}{self.size}s"
        # Формируем и возвращаем пакет
        return struct.pack(dynamic_format, self.pack_type, self.chunk_count, self.stream_id, self.chunk_id, self.size, self.payload)


    @classmethod
    def from_bytes(cls, raw_bytes: bytes):

        # Получаем только заголовок, чтобы узнать длину данных
        header_bytes = raw_bytes[:cls.HEADER_SIZE]
        pack_type, chunk_count, stream_id, chunk_id, size = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Получаем payload по size
        dynamic_format = f"{cls.HEADER_FORMAT}{size}s"
        _, _, payload = struct.unpack(dynamic_format, raw_bytes)

        return cls(pack_type, payload, chunk_count, stream_id, chunk_id)


class PayloadPacket:

    HEADER_FORMAT = "!BH"
    TOTAL_SIZE = struct.calcsize(FORMAT)

    size = None
    pack_type = None
    payload = None


    def __init__(self, pack_type, payload: bytes):

        self.pack_type = pack_type
        self.payload = payload
        self.size = len(payload)


    def to_bytes(self):
        # Динамически упаковывает payload любой длины
        dynamic_format = f"{self.HEADER_FORMAT}{self.size}s"
        # Формируем и возвращаем пакет
        return struct.pack(dynamic_format, self.pack_type, self.size, self.payload)


    @classmethod
    def from_bytes(cls, raw_bytes: bytes):

        # Получаем только заголовок, чтобы узнать длину данных
        header_bytes = raw_bytes[:cls.HEADER_SIZE]
        pack_type, data_size = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Получаем payload по data_size
        dynamic_format = f"{cls.HEADER_FORMAT}{data_size}s"
        _, _, payload = struct.unpack(dynamic_format, raw_bytes)

        return cls(pack_type, payload)

