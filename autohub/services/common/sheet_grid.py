"""Layout-tolerant access to worksheets, so readers find data by label rather than fixed cell."""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Callable, Iterator

_logger = logging.getLogger(__name__)


class LayoutError(ValueError):
    """The sheet does not have the layout this reader expects."""


def column_number(name: str) -> int:
    number = 0
    for character in name.upper():
        number = number * 26 + ord(character) - ord("A") + 1
    return number


def column_letter(number: int) -> str:
    name = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def normalize(value: Any) -> str:
    """Casefolded, whitespace-collapsed text; NFKC folds half-width kana and full-width spaces."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value))).strip().casefold()


def has_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


class SheetGrid:
    """In-memory snapshot of a worksheet's used range, addressed by absolute row/column numbers."""

    def __init__(
        self,
        rows: list[list[Any]],
        first_row: int = 1,
        first_col: int = 1,
        merge_area: Callable[[int, int], tuple[int, int, int, int] | None] | None = None,
    ):
        self._rows = rows
        self.first_row = first_row
        self.first_col = first_col
        self.last_row = first_row + len(rows) - 1
        self.last_col = first_col + max((len(row) for row in rows), default=0) - 1
        self._merge_area = merge_area

    def value(self, row: int, col: int) -> Any:
        r, c = row - self.first_row, col - self.first_col
        if 0 <= r < len(self._rows) and 0 <= c < len(self._rows[r]):
            return self._rows[r][c]
        return None

    def text(self, row: int, col: int) -> str:
        value = self.value(row, col)
        return "" if value is None else str(value).strip()

    def area(self, row: int, col: int) -> tuple[int, int, int, int]:
        """(first_row, first_col, last_row, last_col) of the merged area holding the cell."""
        if self._merge_area is not None:
            area = self._merge_area(row, col)
            if area:
                return area
        return row, col, row, col

    def col_span(self, row: int, col: int) -> tuple[int, int]:
        _, first_col, _, last_col = self.area(row, col)
        return first_col, last_col

    def merged_value(self, row: int, col: int) -> Any:
        """Cell value, or the top-left value of the merged area the cell belongs to."""
        value = self.value(row, col)
        if value is None:
            first_row, first_col, _, _ = self.area(row, col)
            if (first_row, first_col) != (row, col):
                return self.value(first_row, first_col)
        return value

    @classmethod
    def from_com(cls, worksheet) -> "SheetGrid":
        used = worksheet.UsedRange
        data = used.Value
        if not isinstance(data, tuple):  # a one-cell range comes back as a scalar
            data = ((data,),)
        cache: dict[tuple[int, int], tuple[int, int, int, int]] = {}

        def merge_area(row: int, col: int) -> tuple[int, int, int, int]:
            if (row, col) not in cache:
                area = worksheet.Cells(row, col).MergeArea
                cache[(row, col)] = (
                    area.Row,
                    area.Column,
                    area.Row + area.Rows.Count - 1,
                    area.Column + area.Columns.Count - 1,
                )
            return cache[(row, col)]

        return cls([list(row) for row in data], used.Row, used.Column, merge_area)

    @classmethod
    def from_openpyxl(cls, worksheet) -> "SheetGrid":
        areas: dict[tuple[int, int], tuple[int, int, int, int]] = {}
        for merged in worksheet.merged_cells.ranges:
            area = (merged.min_row, merged.min_col, merged.max_row, merged.max_col)
            for row in range(merged.min_row, merged.max_row + 1):
                for col in range(merged.min_col, merged.max_col + 1):
                    areas[(row, col)] = area
        rows = [list(row) for row in worksheet.iter_rows(values_only=True)]
        return cls(rows, 1, 1, lambda row, col: areas.get((row, col)))


def iter_worksheet_groups(workbook) -> Iterator[list]:
    """Worksheets of each embedded Excel object (activated lazily), then the workbook's own."""
    for sheet in workbook.Worksheets:
        try:
            ole_objects = list(sheet.OLEObjects())
        except Exception:
            continue
        for ole_object in ole_objects:
            if not str(ole_object.progID).startswith("Excel.Sheet"):
                continue
            try:
                yield list(ole_object.Object.Worksheets)
            except Exception as error:
                _logger.warning("Could not open embedded object %s: %s", getattr(ole_object, "Name", "?"), error)
    yield list(workbook.Worksheets)


def locate_and_parse(workbook, is_preferred_name: Callable[[str], bool], parse: Callable[[SheetGrid], Any]) -> Any:
    """Parse the first worksheet whose layout matches; name-matched sheets are tried first in each group."""
    errors: list[str] = []
    for sheets in iter_worksheet_groups(workbook):
        names = [sheet.Name for sheet in sheets]
        preferred = [i for i, name in enumerate(names) if is_preferred_name(name)]
        others = [i for i in range(len(sheets)) if i not in preferred]
        for index in preferred + others:
            try:
                return parse(SheetGrid.from_com(sheets[index]))
            except Exception as error:
                if index in preferred:
                    errors.append(f"{names[index]}: {error}")
    detail = "; ".join(errors) if errors else "no sheet matched the expected layout"
    raise LayoutError(f"{detail}. The file may not be this type of document.")
