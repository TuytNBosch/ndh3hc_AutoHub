"""App-wide dark theme: Fusion palette + QSS for inputs/buttons/scrollbars."""
from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

_BG = QColor("#1b1c21")
_BG_ALT = QColor("#24252b")
_TEXT = QColor("#e6e6e6")
_ACCENT = QColor("#2d6cdf")
_DISABLED_TEXT = QColor("#6b6c75")
_PLACEHOLDER_TEXT = QColor("#f0f0f0")

_STYLESHEET = """
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background-color: #2b2c34;
    border: 1px solid #3a3b44;
    border-radius: 4px;
    padding: 4px 6px;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #2d6cdf; }
QPushButton {
    background-color: #2d6cdf;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
}
QPushButton:hover { background-color: #3a7bf0; }
QPushButton:pressed { background-color: #2458b8; }
QPushButton:disabled { background-color: #3a3b44; color: #6b6c75; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #3a3b44; border-radius: 5px; min-height: 20px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, _BG)
    palette.setColor(QPalette.WindowText, _TEXT)
    palette.setColor(QPalette.Base, _BG_ALT)
    palette.setColor(QPalette.AlternateBase, _BG)
    palette.setColor(QPalette.ToolTipBase, _TEXT)
    palette.setColor(QPalette.ToolTipText, _TEXT)
    palette.setColor(QPalette.Text, _TEXT)
    palette.setColor(QPalette.Button, _BG_ALT)
    palette.setColor(QPalette.ButtonText, _TEXT)
    palette.setColor(QPalette.Link, _ACCENT)
    palette.setColor(QPalette.Highlight, _ACCENT)
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.Disabled, QPalette.Text, _DISABLED_TEXT)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, _DISABLED_TEXT)
    palette.setColor(QPalette.PlaceholderText, _PLACEHOLDER_TEXT)

    app.setPalette(palette)
    app.setStyleSheet(_STYLESHEET)


def enable_dark_titlebar(window: QWidget) -> None:
    """Switch the native Windows title bar to dark mode via DWM (Windows 10 1809+/11)."""
    if sys.platform != "win32":
        return

    import ctypes
    from ctypes import wintypes

    hwnd = wintypes.HWND(int(window.winId()))
    value = ctypes.c_int(1)
    for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE: 20 on recent builds, 19 on early 1809
        if ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, wintypes.DWORD(attribute), ctypes.byref(value), ctypes.sizeof(value)
        ) == 0:
            break
