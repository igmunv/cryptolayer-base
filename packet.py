from enum import Enum, auto, unique


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


class Packet:


    HEADER_FORMAT = "!IB"
    TOTAL_SIZE = struct.calcsize(FORMAT)

    size = None
    pack_type = None
    payload = None


    def __init__(self, pack_type, payload):

        self.pack_type = pack_type
        self.payload = payload
        self.size = len(payload)


    def to_bytes(self):
        # Динамически упаковывает payload любой длины
        dynamic_format = f"{self.HEADER_FORMAT}{self.size}s"
        return struct.pack(dynamic_format, self.size, self.pack_type, self.payload)


    @classmethod
    def from_bytes(cls, raw_bytes: bytes):

        # Получаем только заголовок, чтобы узнать длину данных
        header_bytes = raw_bytes[:cls.HEADER_SIZE]
        data_size, pack_type = struct.unpack(cls.HEADER_FORMAT, header_bytes)

        # Получаем payload по data_size
        dynamic_format = f"{cls.HEADER_FORMAT}{data_size}s"
        _, _, payload = struct.unpack(dynamic_format, raw_bytes)

        return cls(pack_type, payload)

