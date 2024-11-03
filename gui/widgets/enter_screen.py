from configparser import ConfigParser
import os
from ssl import SSLSocket

from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QPushButton,
    QToolButton,
    QMainWindow,
    QDialog,
    QLabel,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, Signal

from .components import CustomMenu, ServerDialog


class EnterWidget(QWidget):
    reinit = Signal()

    def __init__(self, stacked_layout, s: SSLSocket | None, window):
        super().__init__()
        self.stacked_layout = stacked_layout
        self.s = s
        self.main_window = window

        layout = QGridLayout()

        self.sign_in_button = QPushButton("Sign In")
        self.sign_up_button = QPushButton("Sign Up")
        self.sign_up_button.setObjectName("reg")
        self.no_connection = QLabel("No connection to the server")
        self.no_connection.setStyleSheet("color: #e03e3e; margin-bottom: 20px")
        self.no_connection.hide()

        if not self.s:
            self.sign_in_button.setDisabled(True)
            self.sign_up_button.setDisabled(True) 
            self.no_connection.show()

        self.options = QToolButton()
        self.options.setFixedSize(30, 30)
        self.options.setIcon(QIcon("./public/options.png"))
        

        self.menu = CustomMenu(offset=True)

        self.config = ConfigParser()
        self.config.read("./gui/config.ini")

        self.servernames = []
        for server in self.config.sections():
            host = self.config.get(server, "host")
            port = self.config.getint(server, "port")
            if server == "Current":
                self.menu.add_action(f"Current server: {host}:{port}", status=False)
                self.menu.add_separator()
                continue

            addr = f"{host}:{port} ({server})"
            self.servernames.append(server)

            self.menu.add_action(
                    addr,
                    lambda _, h=host, p=port: self.change_server(h, p),
                    style="color: #f1f1f1;"
                    )

        self.menu.add_action(
                "Connect to...",
                self.connect_to,
                style="color: #f1f1f1;"
                )
        self.options.setMenu(self.menu)
        self.options.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        buttons = QVBoxLayout()
        buttons.addWidget(self.no_connection, 
                          alignment=Qt.AlignmentFlag.AlignHCenter)
        buttons.addWidget(self.sign_in_button)
        buttons.addSpacing(20)
        buttons.addWidget(self.sign_up_button)

        self.sign_in_button.setMaximumWidth(400)
        self.sign_up_button.setMaximumWidth(400)

        option = QVBoxLayout()
        option.addWidget(
            self.options,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )

        layout.addItem(buttons, 1, 1)
        layout.addItem(option, 0, 2)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnMinimumWidth(1, 300)

        layout.setRowStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.setLayout(layout)

        self.setStyleSheet(
            """
            QPushButton{
                background-color: #2e2e2e;
                height: 45px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 600;
            }
            QToolButton{
                background-color: #2e2e2e;
                border-radius: 6px;
            }
            QPushButton:hover, QToolButton:hover{
                background-color: #3e3e3e;
            }
            QPushButton:pressed, QToolButton:pressed{
                background-color: #5e5e5e;
                }
            QPushButton:disabled{
                background-color: #3e3e3e;
                color: #808080
            }
            QToolButton::menu-indicator{
                image: none;
            }
            #reg{
                background-color: #1e1e1e;
                border: 2px solid #2e2e2e;
            }
            #reg:hover{
                background-color: #3e3e3e;
                border: none;
                color: #1e1e1e;
            }
            #reg:pressed{background-color: #5e5e5e;}
            """
        )

        self.sign_in_button.clicked.connect(self.on_sign_in_clicked)
        self.sign_up_button.clicked.connect(self.on_sign_up_clicked)

    def on_sign_in_clicked(self):
        self.stacked_layout.setCurrentIndex(1)

    def on_sign_up_clicked(self):
        if self.s:
            self.s.send("/signup".encode())
            self.stacked_layout.setCurrentIndex(2)

    def change_server(self, host, port):
        """Changes 'Current' section's options and restarts UI."""

        self.config.set("Current", "host", host)
        self.config.set("Current", "port", str(port))

        with open("./gui/config.ini", "w") as cfg:
            self.config.write(cfg)

        self.reinit.emit()

    def connect_to(self):
        self.dialog = ServerDialog(server_list=self.servernames, parent=self)
        self.main_window.overlay.show()
        parent_geometry = self.window().geometry()
        self.dialog.move(parent_geometry.center() - self.dialog.rect().center())
        self.dialog.exec()

    def _on_dialog_finished(self, result, info=[], add=False):
        self.dialog.hide()
        self.main_window.overlay.hide()

        if result == QDialog.DialogCode.Rejected:
            return

        addr, new_server = info
        host, port = addr.split(":")
        if add:
            if not new_server:
                new_server = str(os.urandom(6))
            self.config.add_section(new_server)
            self.config.set(new_server, "host", host)
            self.config.set(new_server, "port", port)

            with open("./gui/config.ini", "w") as cfg:
                self.config.write(cfg)

        self.change_server(host, port)

    def showEvent(self, event) -> None:
        if isinstance(self.window(), QMainWindow):
            self.main_window.overlay.raise_()
