"""Keeps the leading columns of a QTableWidget visible while the rest scrolls horizontally."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView, QTableWidget


class FrozenColumns:
    """An overlay view over the first `count` columns that shares the table's model and selection."""

    def __init__(self, table: QTableWidget, count: int):
        self._table = table
        self._count = count

        view = QTableView(table)
        view.setModel(table.model())
        view.setSelectionModel(table.selectionModel())
        view.setFocusPolicy(Qt.NoFocus)
        view.verticalHeader().setVisible(False)
        view.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        view.setAlternatingRowColors(True)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollMode(table.verticalScrollMode())
        view.setStyleSheet("QTableView { border: none; border-right: 2px solid #555; }")
        for column in range(count, table.columnCount()):
            view.setColumnHidden(column, True)
        self.view = view
        table.viewport().stackUnder(view)
        view.show()

        table.horizontalHeader().sectionResized.connect(self._on_section_resized)
        table.verticalHeader().sectionResized.connect(lambda row, _old, size: view.setRowHeight(row, size))
        view.verticalScrollBar().valueChanged.connect(table.verticalScrollBar().setValue)
        table.verticalScrollBar().valueChanged.connect(view.verticalScrollBar().setValue)
        self.update_geometry()

    @property
    def width(self) -> int:
        return sum(self._table.columnWidth(column) for column in range(self._count))

    def is_frozen(self, column: int) -> bool:
        return column < self._count

    def _on_section_resized(self, column: int, _old: int, size: int) -> None:
        if self.is_frozen(column):
            self.view.setColumnWidth(column, size)
            self.update_geometry()

    def update_geometry(self) -> None:
        table = self._table
        self.view.setGeometry(
            table.frameWidth(),
            table.frameWidth(),
            self.width,
            table.viewport().height() + table.horizontalHeader().height(),
        )

    def keep_cursor_visible(self, cursor_action, current) -> None:
        """After a left move, scroll so the new cell is not hidden behind the overlay."""
        if cursor_action == QAbstractItemView.MoveLeft and not self.is_frozen(current.column()):
            overshoot = self._table.visualRect(current).left() - self.width
            if overshoot < 0:
                bar = self._table.horizontalScrollBar()
                bar.setValue(bar.value() + overshoot)
