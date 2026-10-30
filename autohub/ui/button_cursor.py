"""Gives every push / tool button of the application a pointing-hand cursor (not while it is disabled)."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QToolButton

_BUTTONS = (QPushButton, QToolButton)
_EVENTS = (QEvent.Polish, QEvent.EnabledChange)


class ButtonCursor(QObject):
    def eventFilter(self, watched, event) -> bool:
        if event.type() in _EVENTS and isinstance(watched, _BUTTONS):
            watched.setCursor(Qt.PointingHandCursor if watched.isEnabled() else Qt.ArrowCursor)
        return False


def install_button_cursor(app: QApplication) -> ButtonCursor:
    """The returned filter must stay referenced for as long as the app runs."""
    cursor = ButtonCursor(app)
    app.installEventFilter(cursor)
    return cursor
