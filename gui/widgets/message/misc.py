from enum import Enum
from typing import TypedDict
from datetime import datetime
from uuid import UUID

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

class MsgType(Enum):
    TEXT = b'TXT'
    IMAGE = b'IMG'
    VIDEO = b'VID'
    DOCUMENT = b'DOC'
    # For unrecognized tags
    UNKNOWN = b'UNK'

class ChunkSize(Enum):
    K64 = 65_536
    K256 = 262_144
    K512 = 524_288
    M1 = 1_048_576

class Tags(TypedDict):
    message_type: MsgType
    message_length: int
    is_file: bool
    basename: str
    chatroom_id: UUID
    timestamp: datetime

def msg_encrypt(data: bytes, pubkey: bytes) -> bytes:
    public_key = RSA.import_key(pubkey)
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)
