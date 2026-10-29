"""Parsing of Bosch HW part-number information (workbooks and email body tables).

Three sources occur in practice and all are matched by header text or token shape, never by fixed
cell positions: the "ECU PN" template workbook (tl_r01_*), the "PN_List" workbook, and tab/space
separated tables pasted into the email body.
"""
import re

from autohub.services.common.sheet_grid import LayoutError, SheetGrid, has_value, normalize

HW_FIELDS = ("hw_ident", "b_number", "customer_order", "field15", "eu_mark", "ss_id", "remark")

_SKIPPED_SHEETS = ("instruction", "old mpx", "history", "sheet1")
_HEADER_SEARCH_ROWS = 40
_HONDA_PART = re.compile(r"^\d{5}-[0-9A-Z]+-[0-9A-Z]+-M6$")
_BOSCH_HW = re.compile(r"^0261S[0-9A-Z]{5}$")
_BOSCH_B = re.compile(r"^0261B[0-9A-Z]{5}(-\d{2})?$")
_FIELD15 = re.compile(r"^\d{5}-[0-9A-Z]+-[0-9A-Z]{2,3}$")
_CODE = re.compile(r"^[0-9A-Z]{3}$")


def normalize_part_number(value) -> str:
    return "" if value is None else re.sub(r"\s+", "", str(value)).upper()


def is_honda_part_number(value) -> bool:
    return bool(_HONDA_PART.match(normalize_part_number(value)))


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


def _record(part_number, source: str, **fields) -> dict:
    record = {"part_number": normalize_part_number(part_number), "source": source}
    record.update({name: _clean(fields.get(name)) for name in HW_FIELDS})
    return record


def _header_row(grid: SheetGrid, required_prefixes: tuple[str, ...]) -> tuple[int, list[str]] | None:
    last = min(grid.last_row, grid.first_row + _HEADER_SEARCH_ROWS)
    for row in range(grid.first_row, last + 1):
        texts = [normalize(grid.value(row, col)) for col in range(grid.first_col, grid.last_col + 1)]
        if all(any(t.startswith(prefix) for t in texts) for prefix in required_prefixes):
            return row, texts
    return None


def _find_columns(grid: SheetGrid, texts: list[str], prefix: str) -> list[int]:
    return [grid.first_col + i for i, text in enumerate(texts) if text.startswith(prefix)]


def parse_ecu_pn_template(grid: SheetGrid, source: str) -> list[dict]:
    """tl_r01 workbook: 'HONDA Parts No.' -> 'Bosch ECU Series P/N' (HW ident) and 'Sample P/N' (B No.)."""
    found = _header_row(grid, ("honda parts no", "bosch ecu series p/n"))
    if found is None:
        raise LayoutError("no 'HONDA Parts No.' / 'Bosch ECU Series P/N' header")
    header_row, texts = found
    honda_col = _find_columns(grid, texts, "honda parts no")[0]
    series_col = _find_columns(grid, texts, "bosch ecu series p/n")[0]
    sample_cols = _find_columns(grid, texts, "bosch ecu sample p/n")
    remark_cols = _find_columns(grid, texts, "remark")

    records = []
    for row in range(header_row + 1, grid.last_row + 1):
        part = grid.value(row, honda_col)
        if not is_honda_part_number(part):
            continue
        records.append(
            _record(
                part,
                source,
                customer_order=part,
                hw_ident=grid.value(row, series_col),
                b_number=grid.value(row, sample_cols[0]) if sample_cols else None,
                remark=grid.value(row, remark_cols[-1]) if remark_cols else None,
            )
        )
    return records


def parse_pn_list(grid: SheetGrid, source: str) -> list[dict]:
    """PN_List workbook: the 'New' block (right-most 'Honda part no.') is the released data."""
    found = _header_row(grid, ("honda part no.", "bosch part no."))
    if found is None:
        raise LayoutError("no 'Honda part no.' / 'Bosch part no.' header")
    header_row, texts = found

    honda_col = _find_columns(grid, texts, "honda part no.")[-1]
    bosch_col = _find_columns(grid, texts, "bosch part no.")[-1]

    def optional(prefix: str) -> int | None:
        cols = _find_columns(grid, texts, prefix)
        return cols[0] if cols else None

    columns = {
        "hw_ident": optional("bosch hw ident"),
        "b_number": optional("bosch hw development"),
        "customer_order": optional("customer order number"),
        "field15": optional("field 15"),
        "eu_mark": optional("field 13"),
        "ss_id": optional("field 14"),
        "remark": optional("remark"),
    }

    records = []
    for row in range(header_row + 1, grid.last_row + 1):
        part = grid.value(row, honda_col)
        if not is_honda_part_number(part):
            continue
        values = {name: grid.value(row, col) if col else None for name, col in columns.items()}
        if not has_value(values["hw_ident"]):
            values["hw_ident"] = grid.value(row, bosch_col)  # older sheets have no separate HW ident column
        values["customer_order"] = values["customer_order"] or part
        records.append(_record(part, source, **values))
    return records


SHEET_PARSERS = (parse_ecu_pn_template, parse_pn_list)


def parse_hw_sheet(grid: SheetGrid, source: str) -> list[dict]:
    errors = []
    for parser in SHEET_PARSERS:
        try:
            return parser(grid, source)
        except LayoutError as error:
            errors.append(str(error))
    raise LayoutError("; ".join(errors))


def is_skipped_sheet(name: str) -> bool:
    return any(marker in normalize(name) for marker in _SKIPPED_SHEETS)


def parse_body_table(text: str, source: str) -> list[dict]:
    """Rows of a table pasted into an email; columns are found by token shape, so delimiters may vary."""
    records = []
    for line in text.splitlines():
        tokens = [t.strip() for t in re.split(r"\t+|\s{2,}", line.strip()) if t.strip()]
        order_index = next((i for i, t in enumerate(tokens) if is_honda_part_number(t)), None)
        if order_index is None:
            continue
        tail = tokens[order_index + 1 :]
        field15 = tail[0] if tail and _FIELD15.match(normalize_part_number(tail[0])) else ""
        codes = tail[1:3] if field15 else []
        record = _record(
            tokens[order_index],
            source,
            customer_order=tokens[order_index],
            hw_ident=next((t for t in tokens if _BOSCH_HW.match(t.upper())), ""),
            b_number=next((t for t in tokens if _BOSCH_B.match(t.upper())), ""),
            field15=field15,
            eu_mark=codes[0] if len(codes) > 0 and _CODE.match(codes[0].upper()) else "",
            ss_id=codes[1] if len(codes) > 1 and _CODE.match(codes[1].upper()) else "",
        )
        # Lines that only mention a part number (quoted history, lists) carry no HW data.
        if any(record[name] for name in ("hw_ident", "b_number", "field15", "eu_mark", "ss_id")):
            records.append(record)
    return records


def merge_records(records: list[dict]) -> list[dict]:
    """One record per part number; earlier sources win, later ones only fill blank fields."""
    merged: dict[str, dict] = {}
    for record in records:
        existing = merged.get(record["part_number"])
        if existing is None:
            merged[record["part_number"]] = {**record, "sources": [record["source"]]}
            continue
        for name in HW_FIELDS:
            if not existing[name] and record[name]:
                existing[name] = record[name]
        if record["source"] not in existing["sources"]:
            existing["sources"].append(record["source"])
    return list(merged.values())
