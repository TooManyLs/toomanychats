from datetime import datetime
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..components import TextBubble, SingleImage, VideoWidget, DocAttachment
from ..utils.tools import generate_name
from . import Tags, MsgType

class MessageRenderer():
    def __init__(self, layout: QVBoxLayout, parent: QWidget) -> None:
        self.layout = layout
        self.p = parent
        self.renderers = {
            MsgType.TEXT: self._render_text_msg,
            MsgType.IMAGE: self._render_img_msg,
            MsgType.VIDEO: self._render_vid_msg,
            MsgType.DOCUMENT: self._render_doc_msg,
            MsgType.UNKNOWN: self._render_unknown_msg,
        }

    def render_message(
            self, header: Tags, msg: bytes = b'',
            pos: int = -1, own: bool = True
    ) -> None:
        # Chooses appropriate function based on the message type
        self.renderers[header['message_type']](header, msg, pos, own)

    def _render_text_msg(
            self, header: Tags, msg: bytes, pos: int, own: bool
    ) -> None:
        timestamp, name, data = self._get_data(header, msg, own)
        message = TextBubble(self.p, data.decode(), name, timestamp)

        # chat_area and send_field are parts of ChatWidget which
        # I cannot import as a type due to the way circular imports
        # are handled in python
        message.chat = self.p.chat_area
        message.sel = self.p.send_field

        self._insert_message(message, pos, own)

    def _render_img_msg(
            self, header: Tags, msg: bytes, pos: int, own: bool
    ) -> None:
        timestamp, name, data = self._get_data(header, msg, own)
        message = SingleImage(self.p, QImage.fromData(data),
                              name, timestamp)

        self._insert_message(message, pos, own)

    def _render_vid_msg(
            self, header: Tags, msg: bytes, pos: int, own: bool
    ) -> None:
        timestamp, name, data = self._get_data(header, msg, own)
        path = save_file(data, header.get('basename', ''))
        message = VideoWidget(path, self.p, name, timestamp)
        self._insert_message(message, pos, own)

    def _render_doc_msg(
            self, header: Tags, msg: bytes, pos: int, own: bool
    ) -> None:
        timestamp, name, data = self._get_data(header, msg, own)
        path = save_file(data, header.get('basename', ''))
        message = DocAttachment(path, name, False, self.p, timestamp)
        self._insert_message(message, pos, own)

    def _render_unknown_msg(
            self, header: Tags, msg: bytes, pos: int, own: bool
    ) -> None:
        timestamp, name, _ = self._get_data(header, msg, own)
        message = TextBubble(self.p, "This message cannot be displayed",
                             name, timestamp, unknown = True)
        self._insert_message(message, pos, own)

    def _insert_message(
            self, message: QWidget, position: int, own: bool
    ) -> None:
        self.layout.insertWidget(position, message,
                                 alignment=(
                                     Qt.AlignmentFlag.AlignRight if own 
                                     else Qt.AlignmentFlag.AlignLeft
                                 )
                             )

    def _get_data(
            self, header: Tags, msg: bytes, own: bool
    ) -> tuple[datetime, str, bytes]:
        # Gets parts of data necessary for widgets to display
        timestamp = header['timestamp']
        name, data = msg.split(b'<SEP>', 1)
        name = "" if own else name.decode()
        
        return timestamp, name, data

def save_file(data: bytes, basename: str = "") -> str:
    if not basename:
        basename = generate_name()
    with open(f"./cache/attachments/{basename}", "wb") as f:
        f.write(data)
    
    return os.path.abspath(f"./cache/attachments/{basename}")
