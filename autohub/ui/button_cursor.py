"""Gives every push / tool button and drop-down list of the application a pointing-hand cursor (not while it is disabled)."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QApplication, QComboBox, QPushButton, QToolButton

_BUTTONS = (QPushButton, QToolButton, QComboBox)
_EVENTS = (QEvent.Polish, QEvent.EnabledChange)


class ButtonCursor(QObject):
    def eventFilter(self, watched, event) -> bool:
        if event.type() in _EVENTS and isinstance(watched, _BUTTONS):
            shape = Qt.PointingHandCursor if watched.isEnabled() else Qt.ArrowCursor
            watched.setCursor(shape)
            if isinstance(watched, QComboBox):
                watched.view().viewport().setCursor(Qt.PointingHandCursor)  # the drop-down list
        return False


def install_button_cursor(app: QApplication) -> ButtonCursor:
    """The returned filter must stay referenced for as long as the app runs."""
    cursor = ButtonCursor(app)
    app.installEventFilter(cursor)
    return cursor
