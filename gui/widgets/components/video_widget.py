import os
import shutil
import subprocess
from datetime import datetime
import platform
from typing import Optional

from PySide6.QtGui import QFontMetrics, QIcon, QPixmap, QPainter
from PySide6.QtWidgets import (
        QApplication, QFileDialog, QLabel, QWidget, QGridLayout,
        QPushButton
)
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QMimeData, Qt, QSize, QTimer, QObject

from . import CustomMenu

class MediaPlayer(QMediaPlayer):
    def __init__(
            self, file: str, video_widget: QVideoWidget,
            parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        
        self.file = file
        self.setSource(file)

        self.audio = QAudioOutput()
        self.audio.setVolume(0.5)
        self.setVideoOutput(video_widget)
        self.setAudioOutput(self.audio)

class VideoWidget(QVideoWidget):
    def __init__(
        self, file: str, parent: QWidget, name: str = "",
            timestamp: datetime = datetime.now()
    ) -> None:
        super().__init__(parent)
        
        self.file = file
        self.par = parent
        self.name_text = name
        self.player = MediaPlayer(file, self)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.player.mediaStatusChanged.connect(self.handleMediaStatus)

        self.source_width = 100
        self.source_height = 100

        self.controls = QGridLayout(self)
        self.controls.setContentsMargins(5,5,5,5)

        self.playpause = QPushButton()
        self.playpause.setFixedSize(40, 40)
        self.playpause.clicked.connect(self.play_pause_toggle)
        self.__round_corners(self.playpause, 20)
        self.playpause.setStyleSheet("background-color: #2e2e2e;")
        self.playpause.hide()

        self.time_text = timestamp.strftime("%I:%M %p")
        self.time = QLabel(self.time_text)
        self.time.setFixedSize(63, 23)
        self.__round_corners(self.time, 10)
        self.time.setObjectName("vid_overlay")
        self.setStyleSheet(
            """
            #vid_overlay, #vid_overlay_btn{
                background-color: #2e2e2e;
                padding: 3px;
                color: white;
            }
            #vid_overlay_btn {
                font-weight: 700;
            }
            """
        )

        self.timer_label = QLabel("")
        self.timer_label.setFixedHeight(23)
        self.timer_label.setObjectName("vid_overlay")

        if name:
            self.name = QPushButton(self.name_text)
            self.name.clicked.connect(lambda: print(f"pushed {self.name_text}"))
            nm_metric = QFontMetrics(self.name.font())
            width = nm_metric.horizontalAdvance(self.name_text) * 1.3
            self.name.setFixedSize(int(width), 23)
            self.__round_corners(self.name, 10)
            self.name.setObjectName("vid_overlay_btn")

            self.controls.addWidget(self.name, 0, 0, 1, 1,
                                    alignment=Qt.AlignmentFlag.AlignLeft 
                                    | Qt.AlignmentFlag.AlignTop)

        self.controls.addWidget(self.timer_label, 0, 3, 1, 1,
                                alignment=Qt.AlignmentFlag.AlignTop
                                | Qt.AlignmentFlag.AlignRight)
        self.controls.addWidget(self.playpause, 1, 0, 1, -1,
                                alignment=Qt.AlignmentFlag.AlignCenter)
        self.controls.addWidget(self.time, 2, 3, 1, -1,
                                alignment=Qt.AlignmentFlag.AlignBottom
                                | Qt.AlignmentFlag.AlignRight)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.playpause.hide)
        self.player.positionChanged.connect(self.update_timer)

    def __round_corners(self, widget: QWidget, radius: float):
        mask = QPixmap(widget.size())
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRoundedRect(widget.rect(), radius, radius)
        painter.end()
        widget.setMask(mask.mask())
        
    def play_pause_toggle(self):
        self.timer.stop()
        if self.player.isPlaying():
            self.player.pause()
            self.playpause.setIcon(QIcon("./public/play.png"))
        else:
            self.player.play()
            self.playpause.setIcon(QIcon("./public/pause.png"))
        self.playpause.show()
        self.timer.start(3000)

    def compute_size(self):
        parent_width = self.par.width()
        old_size = self.size()

        aspect_ratio = self.source_height / self.source_width
        new_width = min(parent_width * 0.8, 500, self.source_width)
        new_height = new_width * aspect_ratio

        if new_height > 600:
            new_height = 600
            new_width = new_height / aspect_ratio

        self.setFixedSize(int(new_width), int(new_height))

        if self.size() != old_size:
            self.__round_corners(self, 12)

    def update_timer(self):
        remaining_time = self.duration - self.player.position()
        minutes, seconds = divmod(remaining_time // 1000, 60)
        time_string = f"{minutes:02}:{seconds:02}"
        self.timer_label.setText(time_string)

        t_metric = QFontMetrics(self.timer_label.font())
        width = t_metric.horizontalAdvance(time_string) * 1.4
        self.timer_label.setFixedWidth(int(width))
        self.__round_corners(self.timer_label, 10)

    def handleMediaStatus(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia: 
            resolution: QSize = self.videoSink().videoSize()
            self.source_width = resolution.width()
            self.source_height = resolution.height()
            self.compute_size()
            
            self.duration = self.player.duration()
            self.short = self.duration // 1000 <= 59

            if self.short:
                self.player.play()
                self.player.setLoops(-1)
            else: 
                self.player.pause()

    def mouseReleaseEvent(self, event):
        pos = event.scenePosition()
        x_in = True if pos.x() > 0 and pos.x() <= self.width() else False
        y_in = True if pos.y() > 0 and pos.y() <= self.height() else False
        if not x_in or not y_in or event.button() != Qt.MouseButton.LeftButton:
            return super().mouseReleaseEvent(event)
        self.play_pause_toggle()
        return super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        self.menu = CustomMenu(self)
        self.menu.add_action("Save as", self.save_as)
        self.menu.add_action("Copy filename", self.copy_name)
        if platform.system() != "Linux":
            self.menu.add_action("Show in Folder", self.show_in_folder)
        self.menu.add_action("Delete", lambda:self.deleteLater()
                             , style="color: #e03e3e;")
        self.menu.exec(event.globalPos())

    def show_in_folder(self):
        abspath = os.path.abspath(self.file)
        if platform.system() == 'Windows':
            subprocess.Popen(f'explorer /select,"{abspath}"')
        else:
            subprocess.Popen(f'open -R "{abspath}"')

    def copy_name(self) -> None:
        mime_data = QMimeData()
        mime_data.setText(self.file)
        QApplication.clipboard().setMimeData(mime_data)

    def save_as(self) -> None:
        default = os.path.basename(self.file)
        _, ext = os.path.splitext(default)
        filters = {
            '.mp4': "MPEG-4 video (*.mp4, *.m4v, *.f4v, *.lrv);;",
            '.m4v': "MPEG-4 video (*.mp4, *.m4v, *.f4v, *.lrv);;",
            '.f4v': "MPEG-4 video (*.mp4, *.m4v, *.f4v, *.lrv);;",
            '.lrv': "MPEG-4 video (*.mp4, *.m4v, *.f4v, *.lrv);;",
        }
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Video", default,
            filter=f"{filters.get(ext, '')}All files (*.*)"
        )
        if filename:
            shutil.copy(self.file, filename)
