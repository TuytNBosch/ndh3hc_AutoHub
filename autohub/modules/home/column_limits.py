"""Keeps every column of the Home table between a minimum and a maximum width, however it was resized."""
from __future__ import annotations

from PySide6.QtWidgets import QTableWidget

MIN_COLUMN_WIDTH = 60
MAX_COLUMN_WIDTH = 300


def clamp_width(width: int, minimum: int = MIN_COLUMN_WIDTH, maximum: int = MAX_COLUMN_WIDTH) -> int:
    return max(minimum, min(width, maximum))


class ColumnLimits:
    def __init__(self, table: QTableWidget, minimum: int = MIN_COLUMN_WIDTH, maximum: int = MAX_COLUMN_WIDTH):
        self._table = table
        self._minimum = minimum
        self._maximum = maximum
        header = table.horizontalHeader()
        header.setMinimumSectionSize(minimum)
        header.setMaximumSectionSize(maximum)
        header.sectionResized.connect(self._on_resized)

    def _on_resized(self, column: int, _old: int, size: int) -> None:
        limited = clamp_width(size, self._minimum, self._maximum)
        if limited != size:
            self._table.setColumnWidth(column, limited)

    def apply(self) -> None:
        """Fits the columns to their content, within the limits."""
        self._table.resizeColumnsToContents()
        for column in range(self._table.columnCount()):
            width = self._table.columnWidth(column)
            limited = clamp_width(width, self._minimum, self._maximum)
            if limited != width:
                self._table.setColumnWidth(column, limited)
