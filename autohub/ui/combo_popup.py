"""Gives every drop-down list a styled item delegate so the theme's highlight and text colours show in its popup."""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QComboBox, QStyledItemDelegate


class ComboPopupStyler(QObject):
    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Polish and isinstance(watched, QComboBox):
            if type(watched.itemDelegate()) is not QStyledItemDelegate:
                watched.setItemDelegate(QStyledItemDelegate(watched))
        return False


def install_combo_popup_style(app: QApplication) -> ComboPopupStyler:
    """The returned filter must stay referenced for as long as the app runs."""
    styler = ComboPopupStyler(app)
    app.installEventFilter(styler)
    return styler
