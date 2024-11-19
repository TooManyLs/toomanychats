import os
from datetime import datetime
from uuid import UUID

from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher

from . import (
    Tags,
    MsgType,
    msg_encrypt,
    FileTags,
    VMediaTags,
    FILELIKE,
    PICTURE_EXT,
)


class HeaderParser():
    def __init__(self, header: bytes, cipher: PKCS1OAEP_Cipher) -> None:
        self._header = header
        self._cipher = cipher
        self._tz = datetime.now().astimezone().tzinfo
        self.tags = self._get_tags()

    def _get_tags(self) -> Tags:
        """
        Walks through the message header bytestring and puts it in
        the appropiate TypedDict or type ```Tags```.
        """
        tags = []
        pos = 0
        while True:
            length = int.from_bytes(self._header[pos:pos+4], "big")
            if length == 0:
                break
            pos += 4

            tag = self._header[pos:pos+length]
            pos += length

            tags.append(tag)

        try:
            msg_type = MsgType(tags[0])
        except ValueError:
            msg_type = MsgType.UNKNOWN

        msg_len = int.from_bytes(tags[1], "big")
        room_id = UUID(bytes=self._decrypt(tags[2]))
        timestamp = datetime.fromtimestamp(
            float(self._decrypt(tags[-1])), self._tz
        )
        
        base_tags = {
            "message_type": msg_type,
            "message_length": msg_len,
            "chatroom_id": room_id,
            "timestamp": timestamp,
        }

        if msg_type not in FILELIKE:
            return Tags(**base_tags)

        basename = self._decrypt(tags[3]).decode()
        dl_id = UUID(bytes=self._decrypt(tags[-2]))

        _, ext = os.path.splitext(basename)
        if msg_type != MsgType.VIDEO and ext not in PICTURE_EXT:
            return FileTags(**{
                **base_tags,
                "basename": basename,
                "download_id": dl_id,
            })

        preview = tags[4] != b'0'

        return VMediaTags(**{
            **base_tags,
            "basename": basename,
            "preview": preview,
            "download_id": dl_id,
        })

    def _decrypt(self, data) -> bytes:
        return self._cipher.decrypt(data)

def generate_header(tags: Tags, public_key: bytes) -> list[bytes]:
    """
    Constructs bytestring header containing information about message.

    Args:
        tags: ```Tags```
            TypedDict of type Tags.
        public_key: ```bytes```
            Public RSA key of recepient.
    """
    tag_list: list[bytes] = []

    msg_type = tags["message_type"]
    room_id = tags["chatroom_id"].bytes
    timestamp = str(tags["timestamp"].timestamp()).encode()

    tag_list.append(msg_type.value)
    tag_list.append(str(tags["message_length"].to_bytes(4, "big")).encode())
    tag_list.append(msg_encrypt(room_id, public_key))

    # Since python does not allow for isinstance check on TypedDict
    # checking type by MsgType and file extension which should be as
    # reliable but ugly
    if msg_type in FILELIKE:
        tag_list.append(msg_encrypt(tags["basename"].encode(), public_key)) #type: ignore

        _, ext = os.path.splitext(tags["basename"]) #type: ignore
        if msg_type == MsgType.VIDEO or ext in PICTURE_EXT:
            tag_list.append(b'1' if tags["preview"] else b'0') #type: ignore

        tag_list.append(msg_encrypt(tags["download_id"].bytes, public_key)) #type: ignore


    tag_list.append(msg_encrypt(timestamp, public_key))

    return tag_list

