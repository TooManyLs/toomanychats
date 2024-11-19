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
    SERVER = b'SRV'
    # For unrecognized tags
    UNKNOWN = b'UNK'

class ChunkSize(Enum):
    K64 = 65_536
    K256 = 262_144
    K512 = 524_288
    M1 = 1_048_576

class Tags(TypedDict):
    """Tags containing basic information about message."""
    message_type: MsgType
    message_length: int
    chatroom_id: UUID
    timestamp: datetime

class FileTags(Tags):
    """Basic Tags with added info about filename/extension and
    ID to request download from the server."""
    basename: str
    download_id: UUID

class VMediaTags(FileTags):
    """File Tags with boolean value of whether message is a preview or not."""
    preview: bool

def msg_encrypt(data: bytes, pubkey: bytes) -> bytes:
    public_key = RSA.import_key(pubkey)
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)

FILELIKE = (MsgType.DOCUMENT, MsgType.IMAGE, MsgType.VIDEO)
PICTURE_EXT = (
    '.bmp', '.cur', '.gif', '.icns', '.ico', '.jpeg', '.jpg', '.pbm', '.pgm',
    '.png', '.ppm', '.tga', '.tif', '.tiff', '.webp', '.xbm', '.jfif', '.dds',
    '.cr2', '.dng', '.heic', '.heif', '.jp2', '.jpe', '.jps', '.nef', '.psd',
    '.ras', '.sgi', '.avif', '.avifs'
)

