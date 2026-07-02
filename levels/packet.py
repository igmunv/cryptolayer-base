from enum import Enum, auto, unique
import struct
import time


class PackTypes(Enum):
    SERVICE = auto()
    COMMUNIC = auto()

class DataTypes(Enum):
    TEXT = auto()
    PHOTO = auto()
    BYTES = auto()

class CMDTypes(Enum):
    PING = auto() # если после последнего сообщения прошло 30 сек, то пингуем. если собеседник отправил сообщение то отчет заново идет
    UPDATE_KEYS = auto()
    DISCONNECT = auto()
    MY_NODE_ID = auto()
    MY_SIGN = auto()
    MY_PUBLIC_KEY = auto()


# Пакет транспортного уровня
class TransportPacket:

    HEADER_FORMAT = "!BBHHQH"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    # Поля заголовка пакета транспортного уровня
    flags = None
    stream_id = None
    chunk_count = None
    chunk_id = None
    time = None
    size = None
    payload = None


    def __init__(self, flags, stream_id, chunk_count, chunk_id, time, payload):
        self.flags = flags
        self.stream_id = stream_id
        self.chunk_count = chunk_count
        self.chunk_id = chunk_id
        self.time = time
        self.size = len(payload)
        self.payload = payload


    # Сериализация пакета в байты
    def to_bytes(self):
        # Динамически упаковывает payload любой длины
        dynamic_format = f"{self.HEADER_FORMAT}{self.size}s"
        # Формируем и возвращаем пакет
        return struct.pack(dynamic_format, self.flags, self.stream_id, self.chunk_count, self.chunk_id, self.time, self.size, self.payload)


    # Десериализация пакета из байтов в класс
    @classmethod
    def from_bytes(cls, raw_bytes: bytes):

        # Получаем только заголовок, чтобы узнать длину данных
        header_bytes = raw_bytes[:cls.HEADER_SIZE]
        flags, stream_id, chunk_count, chunk_id, time, size = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Получаем payload по size
        dynamic_format = f"{cls.HEADER_FORMAT}{size}s"
        _, _, _, _, _, _, payload = struct.unpack(dynamic_format, raw_bytes)

        return cls(flags, stream_id, chunk_count, chunk_id, payload, time)


# Пакет транспортного уровня
class ApplicationPacket:

    HEADER_FORMAT = "!BBH"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    # Поля заголовка пакета транспортного уровня
    pack_type = None
    data_type = None
    size = None
    payload = None


    def __init__(self, pack_type, data_type, payload):
        self.pack_type = pack_type
        self.data_type = data_type
        self.size = len(payload)
        self.payload = payload


    # Сериализация пакета в байты
    def to_bytes(self):
        # Динамически упаковывает payload любой длины
        dynamic_format = f"{self.HEADER_FORMAT}{self.size}s"
        # Формируем и возвращаем пакет
        return struct.pack(dynamic_format, self.pack_type, self.data_type, self.size, self.payload)


    # Десериализация пакета из байтов в класс
    @classmethod
    def from_bytes(cls, raw_bytes: bytes):

        # Получаем только заголовок, чтобы узнать длину данных
        header_bytes = raw_bytes[:cls.HEADER_SIZE]
        print("from_bytes:", cls.HEADER_FORMAT, header_bytes)
        pack_type, data_type, size = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Получаем payload по size
        dynamic_format = f"{cls.HEADER_FORMAT}{size}s"
        _, _, _, payload = struct.unpack(dynamic_format, raw_bytes)

        return cls(pack_type, data_type, payload)
