"""Label-driven parsing of the System Matrix sheet.

Rows are found from their labels (English or Japanese) and variant columns from the part number
row, so layouts with shifted label columns, missing sections or gaps between variants still load.
"""
import re

from autohub.services.common.sheet_grid import (
    LayoutError,
    SheetGrid,
    column_letter,
    column_number,
    has_value,
    normalize,
)

SHEET_PREFIXES = ("システムマトリクス", "system matrix")

_PART_LABELS = {"mass production part number", "量産部番"}
_PROTOTYPE_LABELS = {"prototype part number", "試作部番"}
_DESTINATION_LABELS = {"destination", "仕向け"}
_MARKET_LABELS = {"represented country", "代表国"}
_GENERAL_LABELS = {
    "PartNumber": _PART_LABELS,
    "PrototypePartNumber": _PROTOTYPE_LABELS,
    "Destination": _DESTINATION_LABELS,
    "Market": _MARKET_LABELS,
}
_FORM_B_LABELS = {
    "Hardware": {"hard type", "hardware type"},
    "SSID": {"ssid", "ss-id", "ss id"},
    "ECUMARK": {"eu-mark", "eu mark"},
}
_SETTING_LABELS = {
    "Displacement": {"displacement class"},
    "Transmission": {"transmission"},
    "Emission": {"emission system", "emission regulation"},
}
_ABOLISHED_MARKS = {"廃止", "delete", "deleted"}
_TOP_ROWS = 12
_SECTION_CODE = re.compile(r"^[A-Z]\d{2}$")


def is_system_matrix_sheet(name: str) -> bool:
    return normalize(name).startswith(SHEET_PREFIXES)


def _find_general_labels(grid: SheetGrid) -> dict[str, tuple[int, int]]:
    """field -> (row, right-most label column) for the labels in the header block at the top."""
    found: dict[str, tuple[int, int]] = {}
    last = min(grid.last_row, grid.first_row + _TOP_ROWS)
    for row in range(grid.first_row, last + 1):
        for col in range(grid.first_col, grid.last_col + 1):
            text = normalize(grid.value(row, col))
            for field, labels in _GENERAL_LABELS.items():
                if text in labels and (field not in found or (found[field][0] == row and col > found[field][1])):
                    found[field] = (row, col)
    return found


def _read_general(grid: SheetGrid, labels: dict[str, tuple[int, int]]) -> list[dict]:
    if "PartNumber" not in labels:
        raise LayoutError("part number row (量産部番 / MASS PRODUCTION PART NUMBER) not found")
    part_row, label_col = labels["PartNumber"]
    data_start = label_col + 1
    columns = [c for c in range(data_start, grid.last_col + 1) if has_value(grid.value(part_row, c))]
    if not columns:
        raise LayoutError("no part numbers found next to the part number label")

    rows = []
    for col in columns:
        item = {"Column": column_letter(col)}
        for field, (row, _) in labels.items():
            item[field] = grid.merged_value(row, col)
        above = (normalize(grid.value(r, col)) for r in range(grid.first_row, part_row))
        item["Abolished"] = any(text in _ABOLISHED_MARKS for text in above)
        rows.append(item)
    return rows


def _find_last_label_row(grid: SheetGrid, aliases: set[str], first_row: int, last_col: int) -> int | None:
    for row in range(grid.last_row, first_row - 1, -1):
        if any(normalize(grid.value(row, col)) in aliases for col in range(grid.first_col, last_col + 1)):
            return row
    return None


def _read_form_b(grid: SheetGrid, data_start: int, columns: list[int], first_row: int) -> list[dict]:
    rows_by_field = {
        field: _find_last_label_row(grid, aliases, first_row, data_start - 1)
        for field, aliases in _FORM_B_LABELS.items()
    }
    result = []
    for col in columns:
        item = {"Column": column_letter(col)}
        for field, row in rows_by_field.items():
            value = grid.merged_value(row, col) if row else None
            if field == "Hardware" and isinstance(value, str):
                value = re.sub(r"\s+", "", value)  # "MG1 CA020" is written "MG1CA020" everywhere else
            item[field] = value if has_value(value) else None
        result.append(item)
    return result


def _is_header_row(grid: SheetGrid, row: int, data_start: int) -> bool:
    return any(_SECTION_CODE.match(grid.text(row, col)) for col in range(grid.first_col, data_start))


def _find_section(grid: SheetGrid, aliases: set[str], first_row: int, data_start: int) -> tuple[int, int] | None:
    for row in range(first_row, grid.last_row + 1):
        for col in range(grid.first_col, data_start):
            if normalize(grid.value(row, col)) in aliases and _is_header_row(grid, row, data_start):
                return row, col
    return None


def _read_settings(grid: SheetGrid, data_start: int, columns: list[int], first_row: int) -> list[dict]:
    software_row = next(
        (
            row
            for row in range(first_row, grid.last_row + 1)
            if any(normalize(grid.value(row, c)).startswith("software") for c in range(grid.first_col, data_start))
        ),
        grid.last_row + 1,
    )

    options: dict[str, list[tuple[int, str]]] = {}
    for field, aliases in _SETTING_LABELS.items():
        section = _find_section(grid, aliases, first_row, data_start)
        if section is None:
            options[field] = []
            continue
        header_row, label_col = section
        end = software_row
        for row in range(header_row + 1, software_row):
            if _is_header_row(grid, row, data_start):
                end = row
                break
        options[field] = [
            (row, grid.text(row, label_col)) for row in range(header_row + 1, end) if grid.text(row, label_col)
        ]

    result = []
    for col in columns:
        item = {"Column": column_letter(col)}
        for field, field_options in options.items():
            item[field] = next((text for row, text in field_options if has_value(grid.value(row, col))), None)
        result.append(item)
    return result


def parse_system_matrix(grid: SheetGrid) -> dict:
    labels = _find_general_labels(grid)
    general = _read_general(grid, labels)
    part_row, label_col = labels["PartNumber"]
    data_start = label_col + 1
    columns = [column_number(item["Column"]) for item in general]
    first_row = part_row + 1
    return {
        "GeneralInfo": general,
        "FormB": _read_form_b(grid, data_start, columns, first_row),
        "Setting": _read_settings(grid, data_start, columns, first_row),
    }
