import os
import sys
import atexit
import socket
import ssl
from configparser import ConfigParser

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QStackedLayout,
)
from Crypto.PublicKey import RSA

from widgets import EnterWidget, SignIn, SignUp, ChatWidget
from widgets.components import Overlay


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setWindowTitle("TooManyChats")
     
        self.overlay = Overlay(self)
        self.overlay.hide()     
        self.overlay.setParent(self)
        self.overlay.resize(self.size())

        self.setMinimumWidth(400)
        self.setMinimumHeight(600)

        atexit.register(self.quit)

    def initUI(self) -> None:
        if hasattr(self, "s") and self.s:
            self.s.close()

        # retrieving host and port from config.ini
        config = ConfigParser()
        config.read("./gui/config.ini")
        SERVER_HOST = config.get("Current", "host")
        SERVER_PORT = config.getint("Current", "port")

        self.server_connect((SERVER_HOST, SERVER_PORT))
        self.init_screens()

        container = QWidget()
        container.setLayout(self.stacked_layout)
        self.setCentralWidget(container)

    def server_connect(self, addr: tuple[str, int]) -> None:

        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_path = f"./ssl/servers/{addr[0]}.pem"
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
        self.stacked_layout = QStackedLayout()

        # Screens' initialization
        self.enter_widget = EnterWidget(self.stacked_layout, self.s, self)
        self.sign_in = SignIn(self.stacked_layout, self.s, self.server_pubkey)
        self.sign_up = SignUp(
            self.stacked_layout, self.s, self.server_pubkey, self
        )
        self.main_widget = ChatWidget(
            self.stacked_layout, self.s, self.server_pubkey, self
        )

        self.stacked_layout.addWidget(self.enter_widget)    # 0
        self.stacked_layout.addWidget(self.sign_in)         # 1
        self.stacked_layout.addWidget(self.sign_up)         # 2
        self.stacked_layout.addWidget(self.main_widget)     # 3

        self.sign_in.name_signal.connect(self.main_widget.listen_for_messages)
        self.enter_widget.reinit.connect(self.initUI)
        if self.s:
            self.main_widget.header.reinit.connect(self.initUI)

    def quit(self):
        # Worker thread termination
        if hasattr(self.main_widget, "wk_thread"):
            self.main_widget.wk_thread.quit()
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

    def dragEnterEvent(self, event):
        if event.source():
            return
        try:
            if self.main_widget.dialog.isVisible():
                return
        except AttributeError:
            pass
        if event.mimeData().hasUrls() and self.stacked_layout.currentIndex() == 3:
            for url in event.mimeData().urls():
                if os.path.isdir(url.toLocalFile()):
                    event.ignore()
                    return
            event.acceptProposedAction()
            self.overlay.show()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.overlay.hide()
        return super().dragLeaveEvent(event)

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.main_widget.attach_file(files)


app = QApplication(sys.argv)

window = MainWindow()
window.setStyleSheet(
    """
    QPushButton{color: white;}
    """
)
palette = QPalette()
palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))

app.setPalette(palette)
window.resize(640, 800)
window.show()

app.exec()