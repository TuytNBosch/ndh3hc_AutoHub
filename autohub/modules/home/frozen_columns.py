"""Keeps the leading columns of a QTableWidget visible while the rest scrolls horizontally."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView, QTableWidget


class FrozenColumns:
    """An overlay view over the first `count` columns that shares the table's model and selection.

    `extra` columns (logical indexes) are frozen too and shown right after the leading ones, wherever they are
    in the model."""

    def __init__(self, table: QTableWidget, count: int, extra: tuple[int, ...] = ()):
        self._table = table
        self._count = count
        self._frozen = tuple(range(count)) + tuple(extra)

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
        view.setStyleSheet("QTableView { border: none; border-right: 2px solid palette(mid); }")
        for column in range(table.columnCount()):
            view.setColumnHidden(column, column not in self._frozen)
        for position, column in enumerate(extra, start=count):
            self._move_to(view.horizontalHeader(), column, position)
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
        return sum(self._table.columnWidth(column) for column in self._frozen)

    @staticmethod
    def _move_to(header: QHeaderView, column: int, position: int) -> None:
        header.moveSection(header.visualIndex(column), position)

    def is_frozen(self, column: int) -> bool:
        return column in self._frozen

    def set_hidden(self, column: int, hidden: bool) -> None:
        """Hides or shows a frozen column in the table and in the overlay."""
        # Hidden, a moved section still leaves a gap behind the overlay, so it only sits up front while shown.
        position = self._frozen.index(column) if not hidden else self._table.columnCount() - 1
        self._move_to(self._table.horizontalHeader(), column, position)
        self._table.setColumnHidden(column, hidden)
        self.view.setColumnHidden(column, hidden)
        if not hidden:
            self.view.setColumnWidth(column, self._table.columnWidth(column))
        self.update_geometry()

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
