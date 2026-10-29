"""Maps spreadsheet header cells to (section, field) through a table of rules, so new columns are data."""
from __future__ import annotations

import re
from dataclasses import dataclass

from autohub.services.common.sheet_grid import SheetGrid, has_value, normalize


@dataclass(frozen=True)
class HeaderRule:
    """`pattern` is matched at the start of the normalized header text.

    `occurrence` picks which of several identical headers (e.g. three "MP No.") the rule is for;
    None applies the rule to every match, which a `field` built from group references needs
    (``r"SK\\1"`` maps the SK1, SK2 and SK3 headers to three different fields).
    `edge` chooses the first or last column of a merged header, for headers whose first column
    only holds a caption.
    """

    pattern: str
    section: str
    field: str
    occurrence: int | None = 1
    edge: str = "first"


def map_headers(grid: SheetGrid, row: int, rules: list[HeaderRule]) -> dict[str, dict[str, int]]:
    """section -> field -> column. Rules are tried in order; the first matching pattern claims the cell."""
    patterns = list(dict.fromkeys(rule.pattern for rule in rules))
    seen = {pattern: 0 for pattern in patterns}
    columns: dict[str, dict[str, int]] = {}

    for col in range(grid.first_col, grid.last_col + 1):
        if not has_value(grid.value(row, col)):
            continue
        text = normalize(grid.value(row, col))
        pattern = next((p for p in patterns if re.match(p, text)), None)
        if pattern is None:
            continue
        seen[pattern] += 1
        first_col, last_col = grid.col_span(row, col)
        for rule in rules:
            if rule.pattern == pattern and rule.occurrence in (None, seen[pattern]):
                field = re.match(pattern, text).expand(rule.field)
                columns.setdefault(rule.section, {})[field] = last_col if rule.edge == "last" else first_col
    return columns
