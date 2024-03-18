import os
import sys
import atexit
import socket

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QStackedLayout,
    )
from Crypto.PublicKey import RSA

from widgets import EnterWidget
from widgets import SignIn
from widgets import SignUp
from widgets import ChatWidget
from widgets.components import Overlay

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.s = socket.socket()
        print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}")
        self.s.connect((SERVER_HOST, SERVER_PORT))
        self.server_pubkey = RSA.import_key(self.s.recv(1024))
        print("[+] Connected.")

        self.setWindowTitle("TooManyChats")
        self.overlay = Overlay(self)
        self.overlay.hide()

        self.stacked_layout = QStackedLayout()

        # Screens' initialization
        self.enter_widget = EnterWidget(self.stacked_layout, self.s)
        self.sign_in = SignIn(self.stacked_layout, self.s, self.server_pubkey)
        self.sign_up = SignUp(self.stacked_layout, self.s, self.server_pubkey)
        self.main_widget = ChatWidget(self.stacked_layout, 
                                      self.s, self.server_pubkey)

        self.sign_in.name_signal.connect(self.main_widget.listen_for_messages)

        self.stacked_layout.addWidget(self.enter_widget)    # 0
        self.stacked_layout.addWidget(self.sign_in)         # 1
        self.stacked_layout.addWidget(self.sign_up)         # 2
        self.stacked_layout.addWidget(self.main_widget)     # 3

        container = QWidget()
        container.setLayout(self.stacked_layout)
        self.setCentralWidget(container)
        self.setMinimumWidth(400)
        self.setMinimumHeight(600)

        self.overlay.setParent(self)
        self.overlay.resize(self.size())

        atexit.register(self.quit)

    def quit(self):
        self.s.close()

    def showEvent(self, event):
        self.overlay.resize(self.size())
        event.accept()

    # Keeps dialog in the center of the window
    def moveEvent(self, event):
        if hasattr(self.main_widget, 'dialog'):
            parent_geometry = self.geometry()
            self.main_widget.dialog.move(
                parent_geometry.center() - self.main_widget.dialog.rect().center())

    def resizeEvent(self, event):
        self.overlay.resize(event.size())
    
    def dragEnterEvent(self, event):
        try:
            if self.main_widget.dialog.isVisible():
                return
        except:
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
palette.setColor(QPalette.Window, QColor("#1e1e1e"))
palette.setColor(QPalette.WindowText, QColor("white"))

app.setPalette(palette)
window.resize(1000, 800)
window.show()

app.exec()