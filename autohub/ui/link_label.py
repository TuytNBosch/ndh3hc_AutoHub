"""External link label activated only by a left-button double-click."""
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QMouseEvent
from PySide6.QtWidgets import QLabel


class LinkLabel(QLabel):
    def __init__(self, text: str, url: str):
        super().__init__(text)
        self._url = QUrl(url)
        self.setTextFormat(Qt.PlainText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Double-click to open\n{url}")
        self.setStyleSheet("color: palette(link);")
        font = self.font()
        font.setUnderline(True)
        self.setFont(font)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            QDesktopServices.openUrl(self._url)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
