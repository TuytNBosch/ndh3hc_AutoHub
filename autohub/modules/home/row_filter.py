"""Per-column row filtering rules for the variant table (pure, no Qt)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class ColumnFilter:
    #: case-insensitive "contains" text; empty means no text condition.
    text: str = ""
    #: exact values a cell may have; None means no value condition.
    allowed: frozenset[str] | None = None

    @property
    def active(self) -> bool:
        return bool(self.text) or self.allowed is not None

    def matches(self, cell: str) -> bool:
        if self.text and self.text.casefold() not in cell.casefold():
            return False
        return self.allowed is None or cell in self.allowed


class RowFilter:
    """A row is kept when every column's filter accepts its cell (filters combine with AND)."""

    def __init__(self) -> None:
        self._filters: dict[int, ColumnFilter] = {}

    def get(self, column: int) -> ColumnFilter:
        return self._filters.get(column, ColumnFilter())

    def set(self, column: int, column_filter: ColumnFilter) -> None:
        if column_filter.active:
            self._filters[column] = column_filter
        else:
            self._filters.pop(column, None)

    def is_active(self, column: int | None = None) -> bool:
        return bool(self._filters) if column is None else column in self._filters

    def clear(self) -> None:
        self._filters.clear()

    def matches(self, cells: Sequence[str]) -> bool:
        return all(f.matches(cells[column]) for column, f in self._filters.items() if column < len(cells))
