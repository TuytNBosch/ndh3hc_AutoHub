"""Copy / paste / delete of the selected cells of a QTableWidget as tab-separated text."""
from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QTableWidget


class TableClipboard:
    def __init__(self, table: QTableWidget):
        self._table = table

    def selected_cells(self) -> list[tuple[int, int]]:
        return sorted({(index.row(), index.column()) for index in self._table.selectedIndexes()})

    def is_editable(self, row: int, column: int) -> bool:
        item = self._table.item(row, column)
        return item is not None and bool(item.flags() & Qt.ItemIsEditable)

    def set_cell_text(self, row: int, column: int, text: str) -> bool:
        """Returns True only when the cell actually changed, so no-op writes never flag an edit."""
        if not self.is_editable(row, column):
            return False
        item = self._table.item(row, column)
        if item.text() == text:
            return False
        item.setText(text)
        return True

    def copy_selection(self) -> None:
        cells = self.selected_cells()
        if not cells:
            return
        selected = set(cells)
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        lines = []
        for row in range(min(rows), max(rows) + 1):
            values = []
            for column in range(min(columns), max(columns) + 1):
                item = self._table.item(row, column) if (row, column) in selected else None
                values.append(re.sub(r"[\t\r\n]+", " ", item.text()) if item else "")
            lines.append("\t".join(values))
        QApplication.clipboard().setText("\n".join(lines))

    def paste(self) -> int:
        """Paste tab/newline separated text; returns the number of cells changed."""
        text = QApplication.clipboard().text()
        cells = self.selected_cells()
        if not text or not cells:
            return 0
        grid = [line.split("\t") for line in text.splitlines()]
        if not grid:
            return 0

        if len(grid) == 1 and len(grid[0]) == 1 and len(cells) > 1:
            return sum(self.set_cell_text(row, column, grid[0][0]) for row, column in cells)

        table = self._table
        top = min(row for row, _ in cells)
        left = min(column for _, column in cells)
        changed = 0
        for row_offset, values in enumerate(grid):
            for column_offset, value in enumerate(values):
                row, column = top + row_offset, left + column_offset
                if row < table.rowCount() and column < table.columnCount():
                    changed += self.set_cell_text(row, column, value)
        return changed

    def delete_selection(self) -> int:
        return sum(self.set_cell_text(row, column, "") for row, column in self.selected_cells())
