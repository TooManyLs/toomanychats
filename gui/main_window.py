import os
import sys
import atexit
import socket
import ssl
from ssl import SSLSocket
from configparser import ConfigParser
from pathlib import Path
import tempfile
from uuid import UUID, uuid4

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QStackedLayout,
)
from Crypto.PublicKey import RSA

from widgets import EnterWidget, SignIn, SignUp, ChatWidget
from widgets.components import Overlay, ChatRoomList, Splitter, ScrollArea
from widgets.utils.tools import CLIENT_DIR, qimage_to_bytes

CLIENT_DIR.mkdir(parents=True, exist_ok=True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setWindowTitle("TooManyChats")
     
        self.overlay = Overlay(self)
        self.overlay.hide()     
        self.overlay.setParent(self)
        self.overlay.resize(self.size())

        self.setMinimumWidth(470)
        self.setMinimumHeight(600)

        atexit.register(self.quit)

    def initUI(self) -> None:
        if hasattr(self, "s") and isinstance(self.s, SSLSocket):
            self.s.shutdown(socket.SHUT_RDWR)
            self.s.close()

        # Retrieving host and port from servers.ini
        config = ConfigParser()
        config.read(f"{CLIENT_DIR}/servers.ini")

        # If servers.ini is empty or doesn't exist, write one with defaults
        if not config.sections():
            defaults = ["Current", "localhost"]
            for section in defaults:
                config.add_section(section)
                config.set(section, "host", "127.0.0.1")
                config.set(section, "port", "5002")

            with open(f"{CLIENT_DIR}/servers.ini", "w") as cfg:
                config.write(cfg)

        SERVER_HOST = config.get("Current", "host")
        SERVER_PORT = config.getint("Current", "port")

        self.server_connect((SERVER_HOST, SERVER_PORT))
        self.init_screens()

        container = QWidget()
        container.setLayout(self.stacked_layout)
        self.setCentralWidget(container)

    def server_connect(self, addr: tuple[str, int]) -> None:

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_dir = Path(f"{CLIENT_DIR}/ssl")
        ssl_dir.mkdir(parents=True, exist_ok=True)
        ssl_path = f"{ssl_dir}/{addr[0]}.pem"
        ssl_exist = os.path.exists(ssl_path)

        try:
            self.s = socket.socket()
            print(f"[*] Connecting to {addr[0]}:{addr[1]}")
            self.s.connect(addr)
            cert_len = int.from_bytes(self.s.recv(4), "big")
            cert = self.s.recv(cert_len)

            if ssl_exist:
                with open(ssl_path, "rb") as f:
                    local_ssl = f.read()
                if local_ssl != cert:
                        raise ConnectionRefusedError("SSL certificates doesn't match.")
            else:
                with open(ssl_path, "wb") as f:
                    f.write(cert)

            context.load_verify_locations(ssl_path)
            self.s = context.wrap_socket(self.s, server_hostname="toomanychats")

            self.server_pubkey = RSA.import_key(self.s.recv(1024))
            print("[+] Connected.")
        except ConnectionRefusedError as e:
            print(e)
            self.s = None
            self.server_pubkey = None

    def init_screens(self) -> None:
        if not isinstance(self.s, SSLSocket):
            self.s = None

        self.stacked_layout = QStackedLayout()

        # Screens' initialization
        self.enter_widget = EnterWidget(self.stacked_layout, self.s, self)
        self.sign_in = SignIn(self.stacked_layout, self.s, self.server_pubkey)
        self.sign_up = SignUp(
            self.stacked_layout, self.s, self.server_pubkey, self
        )
        self.main_widget = ChatWidget(
            self.s, self.server_pubkey, self
        )

        # Create the side panel for chat rooms
        self.chat_room_list_widget = ChatRoomList(self)

        self.scl_area = ScrollArea("transparent")
        self.scl_area.setWidget(self.chat_room_list_widget)
        
        # Create a QSplitter to hold the sidebar and the main widget
        self.splitter = Splitter(self)
        self.splitter.addWidget(self.scl_area)
        self.splitter.addWidget(self.main_widget)
        self.splitter.setSizes([240, 400])
        self.splitter.setChildrenCollapsible(False)

        # Set the minimum widths
        self.scl_area.setMinimumWidth(70)
        self.main_widget.setMinimumWidth(400)

        self.stacked_layout.addWidget(self.enter_widget)        # 0
        self.stacked_layout.addWidget(self.sign_in)             # 1
        self.stacked_layout.addWidget(self.sign_up)             # 2
        self.stacked_layout.addWidget(self.splitter)            # 3

        self.sign_in.name_signal.connect(self.main_widget.listen_for_messages)
        self.enter_widget.reinit.connect(self.initUI)
        if self.s:
            self.sign_in.reinit.connect(self.initUI)
            self.main_widget.header.reinit.connect(self.initUI)

        # Only for testing purposes
        from widgets.components.chatroom_item import ChatRoomItem, ChatType
        for x in range(1, 20):
            chatroom = ChatRoomItem(f"chat Room NO_{x}", ChatType.GROUP, uuid4())
            chatroom.room_switch.connect(self.main_widget.change_room)
            self.chat_room_list_widget.list.addWidget(chatroom)

    def quit(self):
        # Worker thread termination
        if hasattr(self.main_widget, "wk_thread"):
            self.main_widget.sender_thread.quit()
            self.main_widget.receiver_thread.quit()
        # Closing socket
        if self.s:
            self.s.close()

    def showEvent(self, event):
        self.overlay.resize(self.size())
        event.accept()

    # Keeps dialog in the center of the window
    def moveEvent(self, event):
        if hasattr(self.main_widget, "dialog"):
            parent_geometry = self.geometry()
            self.main_widget.dialog.move(
                parent_geometry.center() - self.main_widget.dialog.rect().center()
            )

    def resizeEvent(self, event):
        self.overlay.resize(event.size())
        threshold_width = self.chat_room_list_widget.threshold_width
        collapsed_width = self.chat_room_list_widget.collapsed_width

        # Collapse and expand sidebar if it had been constrained by window size
        if self.width() < 640 and not self.chat_room_list_widget.is_collapsed:
            self.splitter.on_splitter_moved(collapsed_width, 1)
            self.chat_room_list_widget.constrained_by_size = True
        if self.width() >= 640 and self.chat_room_list_widget.constrained_by_size:
            self.splitter.on_splitter_moved(threshold_width , 1)
            self.chat_room_list_widget.constrained_by_size = False

        # Set maximum width of the sidebar to half of a widnow width
        self.scl_area.setMaximumWidth(self.width()//2)

        # Keeps the sidebar at a collapsed/threshold width if resizing
        # the window would cause the sidebar to fall between these values
        if self.splitter.sizes()[0] < threshold_width:
            if not self.chat_room_list_widget.is_collapsed:
                self.splitter.setSizes([threshold_width, self.width() - threshold_width])
            else:
                self.splitter.setSizes([collapsed_width, self.width() - collapsed_width])


    def dragEnterEvent(self, event):
        data = event.mimeData()
        if (event.source()
                or self.main_widget.room_id == UUID(int=0)
                or (hasattr(self.main_widget, "dialog")
                    and self.main_widget.dialog.isVisible())
                or not(data.hasUrls() or data.hasImage())
                ):
            # Ignore drag event if either of these is true:
            #   - data being dragged from the same window
            #   - chatroom is closed (uuid of 0)
            #   - attachment dialog window is showing
            #   - dragged data has no image or urls
            event.ignore()
            return
        if data.hasImage():
            pass
        elif (data.hasUrls()
                and isinstance(self.stacked_layout.currentWidget(), Splitter)):
            for url in data.urls():
                if os.path.isdir(url.toLocalFile()):
                    event.ignore()
                    return
        event.acceptProposedAction()
        self.overlay.show()

    def dragLeaveEvent(self, event):
        self.overlay.hide()
        return super().dragLeaveEvent(event)

    def dropEvent(self, event):
        data = event.mimeData()
        if data.hasImage():
            with tempfile.NamedTemporaryFile(
                "w+b", suffix=".webp", delete=False,
                delete_on_close=False
            ) as tmp:
                tmp.write(qimage_to_bytes(data.imageData()))
                files = [tmp.name]
        else:
            files = [u.toLocalFile() for u in data.urls()]

        self.main_widget.attach_file(files)

    def keyPressEvent(self, event) -> None:
        # Shortcuts for splitter screen
        if isinstance(self.stacked_layout.currentWidget(), Splitter):
            if self.main_widget.room_id != UUID(int=0) and event.key() == Qt.Key.Key_Escape:
                self.main_widget.change_room(UUID(int=0).bytes)
        return super().keyPressEvent(event)


app = QApplication(sys.argv)

window = MainWindow()
window.setStyleSheet(
    """
    QPushButton{
        outline: none;
        }
    QSplitter{background-color: #161616;}
    QPushButton, QLabel, QLineEdit, QTextEdit{color: #f1f1f1;}
    QFileDialog QLineEdit{color: black;}
    """
)
palette = QPalette()
palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
palette.setColor(QPalette.ColorRole.WindowText, QColor("#f1f1f1"))

app.setPalette(palette)
window.resize(640, 800)
window.show()

app.exec()
