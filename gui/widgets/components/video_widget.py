from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QWidget
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import Qt, QSize

class VideoWidget(QVideoWidget):
    def __init__(self, file: str, parent: QWidget) -> None:
        super().__init__(parent)
        
        self.file = file
        self.par = parent
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.audio.setVolume(0.5)

        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self)
        self.player.setSource(self.file)

        self.player.mediaStatusChanged.connect(self.handleMediaStatus)

        self.source_width = 100
        self.source_height = 100

    def compute_size(self):
        parent_width = self.par.width()

        aspect_ratio = self.source_height / self.source_width
        new_width = min(parent_width * 0.8, 500, self.source_width)
        new_height = new_width * aspect_ratio

        if new_height > 600:
            new_height = 600
            new_width = new_height / aspect_ratio

        self.setFixedSize(int(new_width), int(new_height))

        mask = QPixmap(self.size())
        mask.fill(Qt.GlobalColor.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRoundedRect(self.rect(), 12, 12)
        painter.end()
        self.setMask(mask.mask())

    def handleMediaStatus(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia: 
            resolution: QSize = self.videoSink().videoSize()
            self.source_width = resolution.width()
            self.source_height = resolution.height()
            self.compute_size()
            
            seconds = round(self.player.duration() / 1000)
            self.short = seconds <= 59
            minutes, seconds = divmod(seconds, 60)
            duration = f"{minutes}:{seconds:02}"

            if self.short:
                self.player.play()
                self.player.setLoops(-1)
            else: 
                self.player.pause()

    def mouseReleaseEvent(self, event):
        pos = event.scenePosition()
        x_in = True if pos.x() > 0 and pos.x() <= self.width() else False
        y_in = True if pos.y() > 0 and pos.y() <= self.height() else False
        if not x_in or not y_in:
            return super().mouseReleaseEvent(event)
        if self.player.isPlaying():
            self.player.pause()
        else:
            self.player.play()
        return super().mouseReleaseEvent(event)