"""Popup where the user picks the text / values to keep for one table column."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from autohub.modules.home.row_filter import ColumnFilter


class ColumnFilterDialog(QDialog):
    def __init__(self, title: str, values: list[str], current: ColumnFilter, parent: QWidget | None = None):
        super().__init__(parent, Qt.Popup)
        self._text = QLineEdit(current.text)
        self._text.setPlaceholderText(f"{title} contains...")
        self._text.setClearButtonEnabled(True)
        self._list = QListWidget()
        for value in values:
            item = QListWidgetItem(value if value else "(Blank)")
            item.setData(Qt.UserRole, value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            checked = current.allowed is None or value in current.allowed
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self._list.addItem(item)
        self._text.textChanged.connect(self._hide_unmatched_values)

        select_all = QPushButton("Select all")
        select_all.clicked.connect(lambda: self._set_visible_checked(True))
        clear_all = QPushButton("Clear all")
        clear_all.clicked.connect(lambda: self._set_visible_checked(False))
        reset = QPushButton("Reset")
        reset.clicked.connect(self._reset)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._text)
        actions = QHBoxLayout()
        for button in (select_all, clear_all, reset):
            actions.addWidget(button)
        layout.addLayout(actions)
        layout.addWidget(self._list)
        layout.addWidget(buttons)
        self.setMinimumWidth(260)
        self._hide_unmatched_values()

    def _items(self):
        return [self._list.item(i) for i in range(self._list.count())]

    def _hide_unmatched_values(self) -> None:
        needle = self._text.text().casefold()
        for item in self._items():
            item.setHidden(bool(needle) and needle not in item.data(Qt.UserRole).casefold())

    def _set_visible_checked(self, checked: bool) -> None:
        for item in self._items():
            if not item.isHidden():
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def _reset(self) -> None:
        self._text.clear()
        self._set_visible_checked(True)

    def result_filter(self) -> ColumnFilter:
        values = [(item.data(Qt.UserRole), item.checkState() == Qt.Checked) for item in self._items()]
        allowed = frozenset(value for value, checked in values if checked)
        everything = len(allowed) == len(values)
        return ColumnFilter(self._text.text(), None if everything else allowed)
