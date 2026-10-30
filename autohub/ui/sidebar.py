"""Collapsible sidebar: logo/title header + icon+label navigation list."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from autohub.config import APP_NAME, ICONS_DIR, LOGO_PATH
from autohub.ui.hover_cursor import HoverCursor

_EXPANDED_WIDTH = 220
_COLLAPSED_WIDTH = 56
_ICON_SIZE = QSize(20, 20)

# Segoe MDL2 Assets glyphs: Cancel (X, shown when open) / GlobalNavButton (hamburger, shown when closed)
_OPEN_GLYPH = "\uE711"
_CLOSED_GLYPH = "\uE700"

_STYLE = """
#Sidebar { background-color: #24252b; }
#sidebarTitle { color: #ffffff; font-size: 15px; font-weight: 600; }
#toggleButton {
    background: transparent; border: none; color: #c7c7d1;
    padding: 0; margin: 0; border-radius: 4px;
}
#toggleButton:hover { color: #ffffff; background-color: #2c2d35; }
#sidebarList { background-color: transparent; border: none; outline: none; font-size: 13px; color: #c7c7d1; }
#sidebarList::item { height: 36px; border-radius: 6px; margin: 2px 8px; padding-left: 6px; }
#sidebarList::item:selected { background-color: #35363f; color: #e2a63c; }
#sidebarList::item:hover:!selected { background-color: #2c2d35; }
"""


class Sidebar(QWidget):
    """Sidebar navigation list that can collapse down to icon-only width."""

    moduleSelected = Signal(int)

    def __init__(self, items: list[tuple[str | None, str]]):
        """``items`` is a list of (icon_file, display_name) pairs, in display order."""
        super().__init__()
        self.setObjectName("Sidebar")
        self._titles = [title for _, title in items]
        self._collapsed = False

        self._logo = QLabel()
        if LOGO_PATH.exists():
            self._logo.setPixmap(QPixmap(str(LOGO_PATH)))
        self._logo.setFixedSize(28, 28)
        self._logo.setScaledContents(True)

        self._title_label = QLabel(APP_NAME)
        self._title_label.setObjectName("sidebarTitle")

        self._toggle_btn = QPushButton(_OPEN_GLYPH)  # sidebar starts expanded
        self._toggle_btn.setObjectName("toggleButton")
        self._toggle_btn.setFont(QFont("Segoe MDL2 Assets", 12))
        self._toggle_btn.setFixedSize(28, 28)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.clicked.connect(self.toggle_collapsed)

        self._header = QHBoxLayout()
        self._header.setContentsMargins(12, 12, 8, 12)
        self._header.addWidget(self._logo)
        self._header.addWidget(self._title_label, stretch=1)
        self._header.addWidget(self._toggle_btn)

        self._list = QListWidget()
        self._list.setObjectName("sidebarList")
        self._list.setFocusPolicy(Qt.NoFocus)
        self._list.setIconSize(_ICON_SIZE)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for icon_file, title in items:
            self._list.addItem(QListWidgetItem(self._resolve_icon(icon_file), title))
        self._list.currentRowChanged.connect(self.moduleSelected)
        self._hover = HoverCursor((self._list,), lambda index: index.isValid())  # hand over the modules

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(self._header)
        layout.addWidget(self._list, stretch=1)

        self.setStyleSheet(_STYLE)
        self.setFixedWidth(_EXPANDED_WIDTH)

        if items:
            self._list.setCurrentRow(0)

    @staticmethod
    def _resolve_icon(icon_file: str | None) -> QIcon:
        path = ICONS_DIR / icon_file if icon_file else None
        return QIcon(str(path)) if path and path.exists() else QIcon()

    def toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        self._toggle_btn.setText(_CLOSED_GLYPH if self._collapsed else _OPEN_GLYPH)
        self.setFixedWidth(_COLLAPSED_WIDTH if self._collapsed else _EXPANDED_WIDTH)
        self._logo.setVisible(not self._collapsed)
        self._title_label.setVisible(not self._collapsed)
        # keep margins tight enough that the toggle button never overflows the collapsed width
        self._header.setContentsMargins(*((4, 12, 4, 12) if self._collapsed else (12, 12, 8, 12)))
        for row, title in enumerate(self._titles):
            self._list.item(row).setText("" if self._collapsed else title)
