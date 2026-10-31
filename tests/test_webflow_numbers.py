from unittest.mock import Mock
from types import SimpleNamespace

import pytest

from autohub.modules.creation.service import WebFlowConfig, WebFlowJobService
from autohub.services.MasterSheet.row_writer import VariantRowWriter
from autohub.services.MasterSheet.webflow_variants import webflow_variant_from_row
from autohub.services.MasterSheet.mx17_layout import home_from_main
from autohub.modules.creation.variant_checklist import VariantChecklist
from tests.fakes import MemorySettings


@pytest.mark.parametrize("columns,addresses", [
    (None, ["AX11", "AW11"]),
    ({"AX": "X", "AW": "Y"}, ["X11", "Y11"]),
])
def test_number_writer_uses_existing_layout_columns_and_preserves_text(columns, addresses):
    worksheet = Mock()
    cells = {address: Mock(HasFormula=False) for address in addresses}
    worksheet.Range.side_effect = cells.__getitem__
    writer = VariantRowWriter(worksheet, Mock())
    assert writer.write_webflow_numbers({"P1": 11}, {"p1": {"AX": "00123", "AW": "ECR42"}}, columns) == 1
    assert cells[addresses[0]].Value == "00123"
    assert cells[addresses[1]].Value == "ECR42"
    assert all(cell.NumberFormat == "@" for cell in cells.values())


def test_number_writer_fails_for_missing_variant_or_formula():
    sheet = Mock()
    writer = VariantRowWriter(sheet, Mock())
    with pytest.raises(ValueError, match="No Master Sheet row"):
        writer.write_webflow_numbers({}, {"P": {"AX": "123"}})
    sheet.Range.return_value.HasFormula = True
    with pytest.raises(ValueError, match="formula"):
        writer.write_webflow_numbers({"P": 11}, {"P": {"AX": "123"}})


@pytest.mark.parametrize("failure", [False, True])
def test_service_writes_numbers_and_returns_explicit_writeback_failure(failure):
    browser = Mock()
    browser.create_and_fill_jobs.return_value = [
        {"PartNumber": "P", "JobId": "42", "SoftwarePartNumber": "00123", "ECRNumber": "ECR42"}
    ]
    sheet = SimpleNamespace(
        open=Mock(), close=Mock(), write_webflow_links=Mock(),
        write_webflow_numbers=Mock(return_value=1),
    )
    if failure:
        sheet.write_webflow_numbers.side_effect = PermissionError("Workbook locked")
    service = WebFlowJobService(Mock(return_value=browser), Mock(return_value=sheet))
    results = service.create_jobs([{"part_number": "P"}], WebFlowConfig("", "", "", ""), master_sheet_path="sheet.xlsx")
    sheet.write_webflow_numbers.assert_called_once_with({"P": {"AX": "00123", "AW": "ECR42"}})
    assert sheet.close.call_count == 2
    assert results[0]["SoftwarePartNumber"] == "00123"
    assert results[0].get("NumberError") == ("Workbook locked" if failure else None)


@pytest.mark.parametrize("mx17", [False, True])
def test_saved_numbers_reload_into_creation_columns(qapp, mx17):
    cells = {"W11": "P", "J11": "P"}

    class Cell:
        HasFormula = False

        def __init__(self, address):
            self.address = address

        @property
        def Value(self):
            return cells.get(self.address)

        @Value.setter
        def Value(self, value):
            cells[self.address] = value

    worksheet = SimpleNamespace(Range=Cell)
    writer = VariantRowWriter(worksheet, None)
    mapping = {"AX": "X", "AW": "Y"} if mx17 else None
    writer.write_webflow_numbers({"P": 11}, {"P": {"AX": "00123", "AW": "ECR42"}}, mapping)
    row = {address[:-2]: value for address, value in cells.items()}
    home = home_from_main(row) if mx17 else row
    variant = webflow_variant_from_row("P", home)
    checklist = VariantChecklist(MemorySettings())
    checklist.set_variants([variant])
    assert checklist._table.item(0, 6).text() == "00123"
    assert checklist._table.item(0, 7).text() == "ECR42"
