from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QPushButton, QToolButton

from autohub.ui.button_cursor import install_button_cursor


def test_buttons_get_a_hand_cursor_while_enabled():
    app = QApplication.instance() or QApplication([])
    keep = install_button_cursor(app)
    push, tool, check = QPushButton("a"), QToolButton(), QCheckBox("c")
    for widget in (push, tool, check):
        widget.ensurePolished()
    assert push.cursor().shape() == Qt.PointingHandCursor
    assert tool.cursor().shape() == Qt.PointingHandCursor
    assert check.cursor().shape() == Qt.ArrowCursor
    push.setEnabled(False)
    assert push.cursor().shape() == Qt.ArrowCursor
    push.setEnabled(True)
    assert push.cursor().shape() == Qt.PointingHandCursor
    app.removeEventFilter(keep)
