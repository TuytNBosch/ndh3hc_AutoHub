"""Rounded-corner banner image that rescales with its width."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QLabel

_BANNER_RADIUS = 14


def _rounded_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(pixmap.rect()), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rounded


class BannerLabel(QLabel):
    def __init__(self, image_path: Path, height: int = 170):
        super().__init__()
        self._source = QPixmap(str(image_path)) if image_path.exists() else QPixmap()
        self.setFixedHeight(height)
        self.setAlignment(Qt.AlignCenter)
        self._refresh()

    def _refresh(self) -> None:
        if self._source.isNull():
            return
        scaled = self._source.scaledToWidth(max(self.width(), 400), Qt.SmoothTransformation)
        self.setPixmap(_rounded_pixmap(scaled, _BANNER_RADIUS))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()
