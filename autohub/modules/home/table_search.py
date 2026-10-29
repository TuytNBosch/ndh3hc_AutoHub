"""Find / replace over a QTableWidget's text cells (no dialog code)."""
from __future__ import annotations

import re

from PySide6.QtWidgets import QTableWidget

#: Column 0 is a display-only row number and is never searched or replaced.
_FIRST_SEARCHABLE_COLUMN = 1


def _contains(text: str, needle: str, match_case: bool) -> bool:
    return needle in text if match_case else needle.lower() in text.lower()


def _replace_in(text: str, needle: str, replacement: str, match_case: bool) -> str:
    flags = 0 if match_case else re.IGNORECASE
    return re.sub(re.escape(needle), lambda _match: replacement, text, flags=flags)


class TableSearch:
    def __init__(self, table: QTableWidget, set_cell_text):
        """`set_cell_text(row, column, text) -> bool` applies an edit and reports whether the cell changed."""
        self._table = table
        self._set_cell_text = set_cell_text

    def find_next(self, needle: str, match_case: bool = False) -> bool:
        """Select the next cell after the current one (row-major, wrapping) containing `needle`."""
        table = self._table
        rows, columns = table.rowCount(), table.columnCount()
        total = rows * columns
        if not total or not needle:
            return False
        has_current = table.currentRow() >= 0 and table.currentColumn() >= 0
        start = table.currentRow() * columns + table.currentColumn() if has_current else -1
        for step in range(1, total + 1):
            row, column = divmod((start + step) % total, columns)
            if column < _FIRST_SEARCHABLE_COLUMN:
                continue
            item = table.item(row, column)
            if item is not None and _contains(item.text(), needle, match_case):
                table.setCurrentCell(row, column)
                return True
        return False

    def replace_current(self, needle: str, replacement: str, match_case: bool = False) -> bool:
        table = self._table
        row, column = table.currentRow(), table.currentColumn()
        item = table.item(row, column) if row >= 0 and column >= 0 else None
        if item is None or not _contains(item.text(), needle, match_case):
            return False
        return self._set_cell_text(row, column, _replace_in(item.text(), needle, replacement, match_case))

    def replace_all(self, needle: str, replacement: str, match_case: bool = False) -> int:
        if not needle:
            return 0
        table = self._table
        changed = 0
        for row in range(table.rowCount()):
            for column in range(_FIRST_SEARCHABLE_COLUMN, table.columnCount()):
                item = table.item(row, column)
                if item is not None and _contains(item.text(), needle, match_case):
                    changed += self._set_cell_text(
                        row, column, _replace_in(item.text(), needle, replacement, match_case)
                    )
        return changed
