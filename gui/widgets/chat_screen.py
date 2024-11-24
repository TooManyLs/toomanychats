import os
from ssl import SSLSocket
import tempfile
from time import sleep
from uuid import UUID
from pathlib import Path

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QSpacerItem, QSizePolicy,
                               QFileDialog, QApplication, QDialog,
                               QFrame
                               )
from PySide6.QtGui import Qt, QIcon, QCursor
from PySide6.QtCore import QMimeData, Slot, QThread, QTimer
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from PIL import UnidentifiedImageError


from .utils.tools import compress_image, qimage_to_bytes, CLIENT_DIR
from .components import (TextBubble, SingleImage, ScrollArea,
                         DocAttachment,AttachDialog,ChatHeader,
                         TextArea, VideoWidget)
from .message import ChunkSize, Tags, MessageRenderer, MsgType
from .utils.services import SenderServiceWorker, ReceiverServiceWorker


buffer_limit = ChunkSize.K256
keys_dir = Path(f"{CLIENT_DIR}/keys")
keys_dir.mkdir(parents=True, exist_ok=True)

class ChatWidget(QWidget):
    def __init__(self, s: SSLSocket | None, 
                 server_pubkey: RsaKey | None, window):
        super().__init__()
        if s is None or server_pubkey is None:
            return
        self.s = s
        self.server_pubkey = server_pubkey.export_key()
        self.main_window = window

        self.scroll_area = ScrollArea()

        self.chat_area = QWidget()
        self.chat_area.setObjectName("scrollarea")
        self.scroll_area.setWidget(self.chat_area)

        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setSpacing(5)
        self.chat_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, 
                        QSizePolicy.Policy.Expanding))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        attach_icon = QIcon("./public/attach.png")
        send_icon = QIcon("./public/send.png")
        self.attach = QPushButton(attach_icon, "")
        self.button = QPushButton(send_icon, "")
        self.send_field = TextArea()
        self.send_field.attach.connect(self.attach_file)
        self.send_field.send.connect(self.on_send)
        self.send_field.setPlaceholderText("Write a message...")
        self.send_field.setObjectName("tarea")
        self.attach.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.inputs = QFrame()
        self.inputs.setObjectName("inputs")
        self.setStyleSheet(
            """
            #inputs{
                background-color: #161616;
            }
            QPushButton{
                border: none;
                border-radius: 6px;
                padding: 7px;
                }
            QPushButton:hover{
                background-color: #2e2e2e;
            }
            #tarea{
                border: none;
            }
            #scrollarea{
                background-color: #1e1e1e;
            }     
            """
            )
        self.scroll_area.setFocusProxy(self.send_field)
        self.attach.setFocusProxy(self.send_field)
        self.button.setFocusProxy(self.send_field)

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(7,7,7,7)
        input_layout.addWidget(self.attach)
        input_layout.addWidget(self.send_field)
        input_layout.addWidget(self.button)
        self.inputs.setLayout(input_layout)

        self.header = ChatHeader(self)
        self.header.getCode.connect(self.on_send)

        main_layout.addWidget(self.header)
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.inputs)

        self.setLayout(main_layout)

        self.button.clicked.connect(self.on_send)
        self.attach.clicked.connect(self.attach_file)

        self.room_id: UUID = UUID(int=1)
        self.change_room(UUID(int=0).bytes)

    def listen_for_messages(self, name: str) -> None:
        self.name = name
        with open(f"{keys_dir}/{name}_private.pem", "rb") as f:
            my_pvtkey = RSA.import_key(f.read())
        self.my_cipher = PKCS1_OAEP.new(my_pvtkey)

        self.recv_worker = ReceiverServiceWorker(
                self.s, self.my_cipher, buffer_limit
                )
        self.receiver_thread = QThread()
        self.recv_worker.moveToThread(self.receiver_thread)
        self.recv_worker.finished.connect(self.receiver_thread.quit)
        self.recv_worker.message_received.connect(self.on_message_received)
        self.receiver_thread.started.connect(self.recv_worker.run)
        self.receiver_thread.start()

        self.send_worker = SenderServiceWorker(
                self.s, self.name, self.server_pubkey, buffer_limit
                )
        self.sender_thread = QThread()
        self.send_worker.moveToThread(self.sender_thread)
        self.sender_thread.start()

        self.renderer = MessageRenderer(self.chat_layout, self)

    def copy_to_clip(self, text: str) -> None:
        mime_data = QMimeData()
        mime_data.setText(text)
        QApplication.clipboard().setMimeData(mime_data)

    @Slot(dict, bytes)
    def on_message_received(self, header: Tags, msg: bytes) -> None:
        commands = {
            "code": self.copy_to_clip
                }
        if header["message_type"] == MsgType.SERVER:
            cmd, data = msg.decode().split("<SEP>")
            commands[cmd](data)
            return

        name = msg.split(b'<SEP>', 1)[0].decode()
        own = name == self.name
        self.renderer.render_message(header, msg, -1, own)
       
    def on_send(self, cmd: str = "") -> None:
        if cmd == "@get_code":
            self.send_worker.send_cmd(b"code", self.room_id)
            return
        to_send: str = self.send_field.toPlainText().strip()
        if to_send:
            bubble = TextBubble(self, to_send)
            bubble.sel = self.send_field
            bubble.chat = self.chat_area
            self.chat_layout.addWidget(bubble, 
                                       alignment=Qt.AlignmentFlag.AlignRight)
            self.send_worker.send_text(to_send.encode(), self.server_pubkey,
                                       self.room_id)
        self.send_field.clear()
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)
    
    def attach_file(self, files: list[str] | None):
        if not files:
            files, _ = QFileDialog().getOpenFileNames(
                self, "Choose Files", 
                filter="All files (*.*)")
        if files:
            try:
                self.dialog = AttachDialog(files, self)
            except UnidentifiedImageError:
                return
            self.main_window.overlay.show()
            self.dialog.show()

    def on_dialog_finished(self, result: QDialog.DialogCode, 
                           files: list[tuple[str, bool]]) -> None:
        self.dialog.hide()
        self.main_window.overlay.hide()
        if result == QDialog.DialogCode.Accepted:
            self.display_attach(files)

    def display_attach(self, files: list[tuple[str, bool]]) -> None:
        for f, pic in files:
            if pic:
                _, ext = os.path.splitext(f)
                if ext != ".gif":
                    compressed = compress_image(f)
                    self.send_worker.send_static_image(
                            qimage_to_bytes(compressed),
                            self.server_pubkey,
                            self.room_id
                    )

                    # Delete temporary file if image was grabbed
                    # from the clipboard
                    temp_dir = tempfile.gettempdir()
                    if temp_dir in f:
                        os.remove(f)
                else:
                    self.send_worker.send_file(f, self.server_pubkey,
                                               self.room_id)
                attachment = SingleImage(self, f)
            else:
                if os.path.splitext(f)[1] == ".mp4":
                    attachment = VideoWidget(f, self)
                else:
                    attachment = DocAttachment(f, parent=self)
                self.send_worker.send_file(f, self.server_pubkey, self.room_id)
            attachment.setFocusProxy(self.send_field)
            self.chat_layout.addWidget(attachment,
                                       alignment=Qt.AlignmentFlag.AlignRight)
            sleep(0.05)
        QApplication.processEvents()
        QTimer.singleShot(1, self.scroll_down)

    def scroll_down(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.scroll_area.old_max = scrollbar.maximum()
        self.scroll_area.relative_position = (
            scrollbar.value() / self.scroll_area.old_max
            if self.scroll_area.old_max > 0 else 0)

    def resizeEvent(self, event):
        if hasattr(self, 'dialog'):
            self.dialog.update_geometry()
            event.accept()
        for c in self.chat_area.children():
            if c.isWidgetType():
                # All widgets in "chat_area" should be resizable
                # so we assume that "c" has "compute_size" attribute
                c.compute_size() #type: ignore

    @Slot(bytes)
    def change_room(self, room_id: bytes) -> None:
        current = self.room_id.bytes
        if room_id == current:
            return

        if room_id == UUID(int=0).bytes: 
            self.inputs.hide()
            self.send_field.setDisabled(True)
        else:
            print("Changed to", self.room_id)
            self.inputs.show()
            self.send_field.setDisabled(False)
        self.room_id = UUID(bytes=room_id)
        self.clear_chat()
        # TODO: change scrollarea's content with contents of current room

    def clear_chat(self) -> None:
        for w in self.chat_area.children()[1:]:
            w.deleteLater()

