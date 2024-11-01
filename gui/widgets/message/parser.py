from datetime import datetime
from uuid import UUID, uuid4

from Crypto.Cipher.PKCS1_OAEP import PKCS1OAEP_Cipher

from . import Tags, MsgType, msg_encrypt


class HeaderParser():
    def __init__(self, header: bytes, cipher: PKCS1OAEP_Cipher) -> None:
        self._header = header
        self._cipher = cipher
        self._tz = datetime.now().astimezone().tzinfo
        self.tags = self._get_tags()

    def _get_tags(self) -> Tags:
        typ = MsgType.TEXT
        basename = ""
        room_id = uuid4()
        timestamp = datetime.now()

        tags = []

        tag_counter = 0
        pos = 0
        while True:
            if len(tags) >= 3:
                if tag_counter > 5:
                    break
            length = int.from_bytes(self._header[pos:pos + 4], "big")
            pos += 4
            tag = self._header[pos:pos + length]
            if not tag:
                break

            tags.append(tag)

            pos += length
            tag_counter += 1

        try:
            typ = MsgType(tags[0])
        except ValueError:
            typ = MsgType.UNKNOWN

        if typ == MsgType.SERVER:
            # Return message_type as the only relevant info for this type
            return Tags(
                message_type = typ,
                message_length = 0,
                is_file = False,
                basename = "",
                chatroom_id = room_id,
                timestamp = timestamp,
            )

        length = int.from_bytes(tags[1])
        is_file = tags[2] != b'0'

        basename = self._decrypt(tags[3]).decode()

        room_id = UUID(bytes=self._decrypt(tags[4]))

        timestamp = datetime.fromtimestamp(
            float(self._decrypt(tags[5])), self._tz
        )

        return Tags(
            message_type = typ,
            message_length = length,
            is_file = is_file,
            basename = basename,
            chatroom_id=room_id,
            timestamp = timestamp,
        )

    def _decrypt(self, data) -> bytes:
        return self._cipher.decrypt(data)

def generate_header(tags: Tags, public_key: bytes) -> list[bytes]:
    tag_list: list[bytes] = []

    basename = tags["basename"].encode()
    room_id = tags["chatroom_id"].bytes
    timestamp = str(tags["timestamp"].timestamp()).encode()

    tag_list.append(tags["message_type"].value)
    tag_list.append(str(tags["message_length"].to_bytes(4, "big")).encode())
    tag_list.append(b'1' if tags["is_file"] else b'0')
    tag_list.append(msg_encrypt(basename, public_key))
    tag_list.append(msg_encrypt(room_id, public_key))
    tag_list.append(msg_encrypt(timestamp, public_key))

    return tag_list

