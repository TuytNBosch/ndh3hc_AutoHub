"""The Mx17 (MED17) master sheet session: flat main sheet plus per-project Info sheets, through Excel COM.

Same interface as `MasterSheet` (the MG1 layout, which is left as it is), so the Home module treats both alike.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from openpyxl.utils import column_index_from_string, get_column_letter

from autohub.core.normalizers import needs_text_format, normalize_part_number
from autohub.core.records import EcuInfoData, HWLookup, KickOffInfo, SystemMatrixData
from autohub.services.common.file_access import write_block_reason
from autohub.services.MasterSheet import mx17_layout as layout
from autohub.services.MasterSheet.MasterSheet import MasterSheet
from autohub.services.MasterSheet.variant_builder import compute_new_variant_rows
from autohub.services.MasterSheet.webflow_variants import webflow_variant_from_row

_XL_CELL_TYPE_CONSTANTS = 2
_XL_READ_WRITE = 2
_LAST_MAIN_INDEX = column_index_from_string(layout.LAST_DATA_COLUMN)
_LAST_INFO_INDEX = column_index_from_string(layout.INFO_LAST_COLUMN)


def _columns(row: tuple, last_index: int) -> dict[str, Any]:
    return {get_column_letter(index + 1): value for index, value in enumerate(row[:last_index])}


class Mx17MasterSheet(MasterSheet):
    sheet_name = layout.MAIN_SHEET_NAME

    def _open_workbook(self, path: str):
        """Opens past a "read-only recommended" flag; a really locked file can still be read, but not written."""
        self.excel_app.DisplayAlerts = False
        self.workbook = self.excel_app.Workbooks.Open(
            path, UpdateLinks=0, ReadOnly=False, IgnoreReadOnlyRecommended=True
        )
        return self.workbook

    def _require_writable(self) -> None:
        if self.workbook.ReadOnly:
            self._try_read_write()
        if self.workbook.ReadOnly:
            reason = write_block_reason(self.file_path) or "Excel opened it read-only (e.g. another Excel holds it)"
            raise PermissionError(f"Workbook is locked or read-only: {reason}. {self.file_path}")

    def _try_read_write(self) -> None:
        """Asks Excel to reopen the workbook read-write; that fails (and it stays read-only) while it is locked."""
        try:
            self.workbook.ChangeFileAccess(Mode=_XL_READ_WRITE)
            self.workbook = self.excel_app.Workbooks(os.path.basename(self.file_path))
        except Exception:  # still locked; the caller reports why
            pass

    # -- Reading ---------------------------------------------------------------------

    def _last_used_row(self, worksheet) -> int:
        used = worksheet.UsedRange
        return used.Row + used.Rows.Count - 1

    def _block(self, worksheet, first_row: int, last_row: int, last_column: str) -> list[tuple]:
        """The cells A{first_row}:{last_column}{last_row} in one call (a COM call per cell would be far too slow)."""
        if last_row < first_row:
            return []
        value = worksheet.Range(f"A{first_row}:{last_column}{last_row}").Value
        return list(value) if value else []

    def _main_rows(self) -> list[tuple[int, dict[str, Any]]]:
        worksheet = self._worksheet()
        first = layout.FIRST_DATA_ROW
        block = self._block(worksheet, first, self._last_used_row(worksheet), layout.LAST_DATA_COLUMN)
        rows = [(first + offset, _columns(row, _LAST_MAIN_INDEX)) for offset, row in enumerate(block)]
        return [(row, values) for row, values in rows if normalize_part_number(values.get(layout.PART_NUMBER_COLUMN))]

    def _info_sheets(self) -> list:
        sheets = []
        for index in range(1, self.workbook.Worksheets.Count + 1):
            worksheet = self.workbook.Worksheets(index)
            marker = worksheet.Range(f"{layout.INFO_MARKER_COLUMN}{layout.INFO_HEADER_ROW}").Value
            if isinstance(marker, str) and layout.INFO_MARKER_TEXT in marker:
                sheets.append(worksheet)
        return sheets

    def _info_rows(self) -> dict[str, tuple[Any, int, dict[str, Any]]]:
        """Upper-case part number -> (Info sheet, row, {column: value}); the last row of a part number wins."""
        found: dict[str, tuple[Any, int, dict[str, Any]]] = {}
        marker_index = column_index_from_string(layout.INFO_MARKER_COLUMN) - 1
        for worksheet in self._info_sheets():
            first = layout.INFO_FIRST_DATA_ROW
            block = self._block(worksheet, first, self._last_used_row(worksheet), layout.INFO_LAST_COLUMN)
            for offset, row in enumerate(block):
                part_number = normalize_part_number(row[0])
                if part_number and row[marker_index] not in (None, ""):  # title rows have no Delivery Type
                    found[part_number.upper()] = (worksheet, first + offset, _columns(row, _LAST_INFO_INDEX))
        return found

    def _loaded_variants(self) -> list[tuple[int, dict, Any]]:
        """(main sheet row, Home table values, created date), the latest row per part number."""
        info = self._info_rows()
        latest: dict[str, tuple[int, dict, Any]] = {}
        for row, values in self._main_rows():
            home = layout.home_from_main(values)
            part_number = home["J"] = normalize_part_number(home["J"])
            if part_number.upper() in info:
                home.update(layout.home_overlay_from_info(info[part_number.upper()][2]))
            latest[part_number.upper()] = (row, home, values.get("B"))
        return list(latest.values())

    def load_variant_rows(self) -> list[dict]:
        return [{"_row": row, **home} for row, home, _created in self._loaded_variants()]

    def load_webflow_variants(self) -> list[dict]:
        return [
            webflow_variant_from_row(home["J"], {**home, "C": created})
            for _row, home, created in self._loaded_variants()
        ]

    # -- New variants ----------------------------------------------------------------

    def compute_new_variants(
        self,
        system_info: SystemMatrixData,
        ecu_info: EcuInfoData,
        hw_info: HWLookup | None = None,
        kick_off: KickOffInfo | None = None,
    ) -> list[dict]:
        """Variants whose part number is not in the main sheet yet (the Purpose column is free text here)."""
        known = {normalize_part_number(values.get(layout.PART_NUMBER_COLUMN)).upper() for _row, values in self._main_rows()}
        rows = compute_new_variant_rows(ecu_info, system_info, set(), hw_info, kick_off=kick_off)
        return [row for row in rows if normalize_part_number(row.get("J")).upper() not in known]

    # -- Writing ---------------------------------------------------------------------

    def save_variant_rows(self, variants: list[dict], save: bool = True) -> list[dict]:
        """A "_row" entry updates that main sheet row (and its Info row); otherwise a row is appended to both."""
        self._require_writable()
        worksheet = self._worksheet()
        info = self._info_rows()
        saved = []
        for variant in variants:
            home = {key: value for key, value in variant.items() if not key.startswith("_")}
            row = variant.get("_row")
            if row:
                row = int(row)
                self._write(worksheet, row, layout.main_values_from_home(home))
                known = info.get(normalize_part_number(home.get("J")).upper())
                if known:
                    self._write(known[0], known[1], layout.info_values_from_home(home))
            else:
                row = self._append_main_row(worksheet)
                self._write(worksheet, row, layout.new_main_values(home, datetime.now()))
                self._append_info_row(home)
            saved.append({"PartNumber": home.get("J"), "RequestRow": row})
        if save:
            self.save()
        return saved

    def delete_variant_rows(self, request_rows: list[int], save: bool = True) -> int:
        """Delete the main sheet rows (one per variant), bottom up; a row without a part number is skipped."""
        self._require_writable()
        worksheet = self._worksheet()
        deleted = 0
        for row in sorted({int(row) for row in request_rows}, reverse=True):
            if row < layout.FIRST_DATA_ROW or not worksheet.Range(f"{layout.PART_NUMBER_COLUMN}{row}").Value:
                continue
            worksheet.Rows(row).Delete()
            deleted += 1
        if save and deleted:
            self.save()
        return deleted

    def _write(self, worksheet, row: int, values: dict[str, Any]) -> None:
        for column, value in values.items():
            cell = worksheet.Range(f"{column}{row}")
            if cell.HasFormula:
                continue  # formulas (running number, hex of the program id) stay as they are
            if needs_text_format(value):
                cell.NumberFormat = "@"  # keep leading zeros and values like 4E5 as typed
            cell.Value = value

    def _copy_row_below(self, worksheet, row: int, last_column: str) -> int:
        """Copies `row` (formats and formulas) to the row below and clears the copied constants."""
        new_row = row + 1
        worksheet.Rows(row).Copy(worksheet.Rows(new_row))
        self.excel_app.CutCopyMode = False
        try:
            worksheet.Range(f"A{new_row}:{last_column}{new_row}").SpecialCells(_XL_CELL_TYPE_CONSTANTS).ClearContents()
        except Exception:  # no constants to clear
            pass
        return new_row

    def _append_main_row(self, worksheet) -> int:
        last = layout.FIRST_DATA_ROW - 1
        for row, _values in self._main_rows():
            last = max(last, row)
        return self._copy_row_below(worksheet, last, layout.LAST_DATA_COLUMN)

    def _find_sheet(self, name: str):
        for index in range(1, self.workbook.Worksheets.Count + 1):
            if self.workbook.Worksheets(index).Name == name:
                return self.workbook.Worksheets(index)
        return None

    def _new_info_sheet(self, name: str, title: str):
        """A new Info sheet for a project: the Mx17 Info sheet (else the first one) without its variants."""
        sheets = self._info_sheets()
        if not sheets:
            raise RuntimeError("The Master Sheet has no Info sheet to copy for the new project.")
        template = next((sheet for sheet in sheets if sheet.Name == layout.INFO_TEMPLATE_SHEET), sheets[0])
        template.Copy(After=sheets[-1])
        worksheet = self.workbook.ActiveSheet
        worksheet.Name = name
        last = max(self._last_used_row(worksheet), layout.INFO_TITLE_ROW)
        worksheet.Range(f"A{layout.INFO_TITLE_ROW}:{layout.INFO_LAST_COLUMN}{last}").ClearContents()
        worksheet.Range(f"A{layout.INFO_TITLE_ROW}").Value = title
        return worksheet

    def _append_info_row(self, home: dict) -> None:
        name = layout.info_sheet_name(home.get("AB"))
        worksheet = self._find_sheet(name)
        if worksheet is None:
            worksheet = self._new_info_sheet(name, home.get("H") or name)
            row = layout.INFO_FIRST_DATA_ROW
        else:
            last = layout.INFO_FIRST_DATA_ROW - 1
            for offset, values in enumerate(
                self._block(worksheet, layout.INFO_FIRST_DATA_ROW, self._last_used_row(worksheet), "A")
            ):
                if values[0] not in (None, ""):
                    last = layout.INFO_FIRST_DATA_ROW + offset
            row = (
                self._copy_row_below(worksheet, last, layout.INFO_LAST_COLUMN)
                if last >= layout.INFO_FIRST_DATA_ROW
                else layout.INFO_FIRST_DATA_ROW
            )
        self._write(worksheet, row, layout.info_values_from_home(home, defaults_for_blanks=True))
