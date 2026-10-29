"""Header-driven parsing of the ECU Info Sheet "Factory_event" sheet.

Columns are located from the header row ("Event", "MP No.", "PART NO." ...) rather than fixed
letters, so sheets with shifted columns or without some columns (e.g. no Security Key) still load.
"""
import re

from autohub.services.common.header_rules import HeaderRule, map_headers
from autohub.services.common.sheet_grid import LayoutError, SheetGrid, has_value, normalize

SHEET_NAME = "factory_event"

# Header text -> (section, field). Order matters: the first pattern that matches a cell claims it,
# so "immobi code config" must precede "immobi". To read a new column, add a rule here.
# "MP No." and the ID headers repeat; their occurrence selects ecu / main / boot.
HEADER_RULES = [
    HeaderRule(r"event\b", "ecu", "Event"),
    HeaderRule(r"mp no", "ecu", "MP", occurrence=1),
    HeaderRule(r"mp no", "main", "MP", occurrence=2),
    HeaderRule(r"mp no", "boot", "MP", occurrence=3),
    HeaderRule(r"ecu hard type", "ecu", "EcuHardware"),
    HeaderRule(r"ccp measurement", "ecu", "CCPMeasurement"),
    HeaderRule(r"ccp can1 or ccp can2", "ecu", "CCPCanChannel"),
    HeaderRule(r"vin diag", "ecu", "VINDiag"),
    HeaderRule(r"immobi code config", "ecu", "ImmobiCodeConfig"),
    HeaderRule(r"immobi", "ecu", "Immobi"),
    HeaderRule(r"security key identifier", "ecu", "SecurityKeyIdentifier"),
    HeaderRule(r"security key", "ecu", "SecurityKey"),
    HeaderRule(r"pver name", "ecu", "PVERName"),
    HeaderRule(r"rom check", "ecu", "ROMCheck"),
    HeaderRule(r"tuning protection", "ecu", "TuningProtection"),
    HeaderRule(r"lv2 monitoring", "ecu", "Lv2Monitoring"),
    HeaderRule(r"fi-tm version check", "ecu", "FITMVersionCheck"),
    # The span's first column only holds a caption, the value is in the last one.
    HeaderRule(r"description by drawing", "container", "DescriptionByDrawing", edge="last"),
    HeaderRule(r"destination", "container", "Destination"),
    HeaderRule(r"ecu label", "container", "EcuLabel"),
    HeaderRule(r"part no", "main", "NumCompID"),
    HeaderRule(r"calibration id", "main", "NumProgID", occurrence=1),
    HeaderRule(r"calibration id", "boot", "NumProgID", occurrence=2),
    HeaderRule(r"diagnosis id", "main", "NumReWrecuid", occurrence=1),
    HeaderRule(r"diagnosis id", "boot", "NumReWrecuid", occurrence=2),
    HeaderRule(r"security type.*\bsk([123])\b", "boot", r"SK\1", occurrence=None),
]
ECU_FIELDS = list(
    dict.fromkeys(["Event", "MP", *(rule.field for rule in HEADER_RULES if rule.section == "ecu")])
)
_EXAMPLE_ROW_LABELS = {"example", "calibration label"}
_HEADER_SEARCH_ROWS = 60
_GENERAL_SEARCH_ROWS = 15


def _find_header_row(grid: SheetGrid) -> int:
    last = min(grid.last_row, grid.first_row + _HEADER_SEARCH_ROWS)
    for row in range(grid.first_row, last + 1):
        texts = [normalize(grid.value(row, col)) for col in range(grid.first_col, grid.last_col + 1)]
        if (
            any(re.match(r"event\b", t) for t in texts)
            and any(t.startswith("mp no") for t in texts)
            and any(t.startswith("part no") for t in texts)
        ):
            return row
    raise LayoutError("header row with Event / MP No. / PART NO. not found")


def _read_headers(grid: SheetGrid, row: int) -> dict[str, dict[str, int]]:
    columns = map_headers(grid, row, HEADER_RULES)
    sections = {name: columns.get(name, {}) for name in ("ecu", "container", "main", "boot")}
    if "Event" not in sections["ecu"] or "NumCompID" not in sections["main"]:
        raise LayoutError("Event or PART NO. column not found in the header row")
    return sections


def _read_general_info(grid: SheetGrid, header_row: int) -> dict:
    """The value sits immediately left of its label, e.g. [27.0MY][MY][62XS][Project]."""
    labels = {"MY": "my", "Project": "project"}
    found: dict[str, object] = {}
    last = min(header_row, grid.first_row + _GENERAL_SEARCH_ROWS)
    for row in range(grid.first_row, last + 1):
        for col in range(grid.first_col + 1, grid.last_col + 1):
            text = normalize(grid.value(row, col))
            for field, label in labels.items():
                if text == label and field not in found:
                    found[field] = grid.merged_value(row, col - 1)
    if "Project" not in found:
        raise LayoutError("Project label not found above the header row")
    return {"MY": found.get("MY"), "Project": found["Project"]}


def parse_ecu_info(grid: SheetGrid) -> dict:
    header_row = _find_header_row(grid)
    columns = _read_headers(grid, header_row)
    ecu_cols, container_cols = columns["ecu"], columns["container"]
    main_cols, boot_cols = columns["main"], columns["boot"]

    event_col = ecu_cols["Event"]
    first_data_row = header_row + 1
    while first_data_row <= grid.last_row and normalize(grid.value(first_data_row, event_col)) in _EXAMPLE_ROW_LABELS:
        first_data_row += 1

    section_cols = [c for cols in (container_cols, main_cols, boot_cols) for c in cols.values()]
    rows: list[int] = []
    row = first_data_row
    while row <= grid.last_row and any(has_value(grid.value(row, c)) for c in section_cols):
        rows.append(row)
        row += 1
    # Trailing rows holding only "-" placeholders (e.g. in the Boot columns) are not variants.
    part_col = main_cols["NumCompID"]
    while rows and not has_value(grid.value(rows[-1], part_col)):
        rows.pop()
    if not rows:
        raise LayoutError("no variant rows found below the header row")

    def read(r: int, cols: dict[str, int]) -> dict:
        return {field: grid.merged_value(r, col) for field, col in cols.items()}

    container = [{**read(r, container_cols), "Row": r} for r in rows]
    boot = [{**read(r, boot_cols), "Row": r} for r in rows]
    main = []
    for r in rows:
        values = read(r, main_cols)
        values["CALIBID"] = values.get("NumProgID")  # same cell as the program id, as in the legacy reader
        main.append({**values, "Row": r})

    # A new ECU group starts where the Event or MP cell holds its own value (merged cells hold it once).
    mp_col = ecu_cols.get("MP")
    starts = [
        i
        for i, r in enumerate(rows)
        if i == 0 or has_value(grid.value(r, event_col)) or (mp_col and has_value(grid.value(r, mp_col)))
    ]
    ecu_groups = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(rows)
        values = {field: None for field in ECU_FIELDS}
        values.update(read(rows[start], ecu_cols))
        ecu_groups.append({**values, "Rows": rows[start:end]})

    return {
        "GeneralInfo": [_read_general_info(grid, header_row)],
        "Ecu": ecu_groups,
        "Container": container,
        "Main": main,
        "Boot": boot,
    }


_ENGINE_FAMILY_LABEL = "engine family"
_CR_END_LABEL = "confirm at project kickoff"


def parse_engine_family(grid: SheetGrid) -> str:
    """Engine family of the "Issue CR" sheet: the entry whose YES flag sits under an "Engine family" header."""
    headers = [
        (row, col)
        for row in range(grid.first_row, grid.last_row + 1)
        for col in range(grid.first_col, grid.last_col + 1)
        if normalize(grid.value(row, col)) == _ENGINE_FAMILY_LABEL
    ]
    if not headers:
        raise LayoutError("Engine family header not found")
    header_columns = {col for _, col in headers}
    for row in range(headers[0][0] + 1, grid.last_row + 1):
        if any(normalize(grid.value(row, col)).startswith(_CR_END_LABEL) for col in range(grid.first_col, grid.last_col + 1)):
            break
        for col in header_columns:
            if normalize(grid.value(row, col)) != "yes":
                continue
            for next_col in range(col + 1, grid.last_col + 1):
                lines = grid.text(row, next_col).splitlines()
                if lines:
                    return lines[0].strip()
    raise LayoutError("no engine family is marked YES")
