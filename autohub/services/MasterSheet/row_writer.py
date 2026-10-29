"""Writes request rows into the Master Sheet worksheet (COM): insert from the template or update in place."""
from __future__ import annotations

from datetime import datetime

from autohub.core.normalizers import needs_text_format

LAST_DATA_COLUMN = "CZ"
_ROWS_PER_VARIANT = 3  # request, implementation and comparison rows
_INSERT_SHIFT_DOWN = -4121  # xlShiftDown
_TEMPLATE_ROW_TYPES = {"REQ", "IMPL"}
_PRESERVED_COLUMNS = {2, 4}  # No. and the REQ/IMPL mark


class VariantRowWriter:
    def __init__(self, worksheet, excel_app):
        self._worksheet = worksheet
        self._excel_app = excel_app

    def copy_one_variant_template(self, row_count: int = _ROWS_PER_VARIANT) -> dict:
        """Copy the last `row_count` rows below themselves as an empty variant; returns the row ranges."""
        if row_count < 1:
            raise ValueError("row_count must be greater than zero.")

        worksheet = self._worksheet
        used = worksheet.UsedRange
        last_row = used.Row + used.Rows.Count - 1
        first_row = last_row - row_count + 1
        if first_row < used.Row:
            raise ValueError("The worksheet does not contain enough rows to copy.")

        destination_row = last_row + 1
        worksheet.Rows(f"{first_row}:{last_row}").Copy()
        inserted_rows = f"{destination_row}:{destination_row + row_count - 1}"
        worksheet.Rows(inserted_rows).Insert(Shift=_INSERT_SHIFT_DOWN)
        self._excel_app.CutCopyMode = False
        self._clear_copied_values(destination_row, destination_row + row_count - 1)
        return {"SourceRows": f"{first_row}:{last_row}", "InsertedRows": inserted_rows}

    def save_rows(self, variants: list[dict]) -> list[dict]:
        """Write each (possibly user-edited) row; a "_row" entry updates that row, otherwise a new one is inserted."""
        saved = []
        for variant in variants:
            existing_row = variant.get("_row")
            values = {key: value for key, value in variant.items() if not key.startswith("_")}

            if existing_row:
                request_row = int(existing_row)
                self.write_values(request_row, values)
            else:
                copied = self.copy_one_variant_template()
                request_row = int(copied["InsertedRows"].split(":", 1)[0])
                self.write_values(request_row, {**values, "C": datetime.now()})

            saved.append(
                {
                    "PartNumber": values.get("J"),
                    "RequestRow": request_row,
                    "ImplementationRow": request_row + 1,
                    "ComparisonRow": request_row + 2,
                }
            )
        return saved

    def write_values(self, row: int, values: dict) -> None:
        worksheet = self._worksheet
        last_data_column = worksheet.Range(f"{LAST_DATA_COLUMN}1").Column
        for column_name, value in values.items():
            if value in (None, ""):
                continue
            cell = worksheet.Range(f"{column_name}{row}")
            if cell.Column <= last_data_column and not cell.HasFormula:
                if needs_text_format(value):
                    cell.NumberFormat = "@"  # keep leading zeros and values like 4E5 as typed
                cell.Value = value

    def _clear_copied_values(self, first_row: int, last_row: int) -> None:
        worksheet = self._worksheet
        last_column = worksheet.Range(f"{LAST_DATA_COLUMN}1").Column
        for row in range(first_row, last_row + 1):
            if str(worksheet.Cells(row, 4).Value).strip().upper() not in _TEMPLATE_ROW_TYPES:
                continue
            for column in range(worksheet.UsedRange.Column, last_column + 1):
                cell = worksheet.Cells(row, column)
                if column not in _PRESERVED_COLUMNS and not cell.HasFormula:
                    cell.ClearContents()
