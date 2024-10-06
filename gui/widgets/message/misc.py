from enum import Enum


class MsgType(Enum):
    TEXT = b'TXT'
    IMAGE = b'IMG'
    VIDEO = b'VID'
    DOCUMENT = b'DOC'

class ChunkSize(Enum):
    K64 = 65_536
    K256 = 262_144
    K512 = 524_288
    M1 = 1_048_576

