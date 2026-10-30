"""Shows a pointing-hand cursor while the mouse is over an item that `is_link(index)` accepts."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QAbstractItemView


class HoverCursor(QObject):
    def __init__(self, views: tuple[QAbstractItemView, ...], is_link):
        """`is_link(index)` tells whether the item under the mouse is clickable."""
        super().__init__(views[0])
        self._is_link = is_link
        for view in views:
            view.setMouseTracking(True)
            view.viewport().setMouseTracking(True)
            view.viewport().installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.MouseMove:
            index = watched.parent().indexAt(event.position().toPoint())
            watched.setCursor(Qt.PointingHandCursor if self._is_link(index) else Qt.ArrowCursor)
        elif event.type() == QEvent.Leave:
            watched.setCursor(Qt.ArrowCursor)
        return False
