from PySide6.QtWidgets import QLabel

from autohub.modules.creation.variant_checklist import VariantChecklist
from tests.fakes import MemorySettings


def test_creation_headers_and_ecu_values(qapp):
    checklist = VariantChecklist(MemorySettings())
    checklist.set_variants([{
        "part_number": "P", "ecu_type": "MG1CS022",
        "ecu": {"family_name": "MG1CS022", "project_version": "6WZX", "program_version": "V037"},
    }])
    table = checklist._table
    assert [table.horizontalHeaderItem(col).text() for col in range(6)] == [
        "Select", "Part Number", "Family Name", "FSWID Project Version", "FSWID Program Version", "WebFlow Link",
    ]
    assert [table.item(0, col).text() for col in range(1, 5)] == [
        "P", "MG1CS022", "6WZX", "V037",
    ]
    assert table.showGrid()
    assert checklist._checkboxes["P"].text() == ""
    assert not any(label.text().startswith("Variants (") for label in checklist.findChildren(QLabel))
    checklist._checkboxes["P"].setChecked(True)
    checklist.set_links({"P": "https://webflow/app/ShowJob/42"})
    assert checklist._checkboxes["P"].isChecked()
    assert table.cellWidget(0, 5).text() == "WF42"
    assert table.item(0, 3).text() == "6WZX"


def test_missing_ecu_values_and_event_filter(qapp):
    checklist = VariantChecklist(MemorySettings())
    checklist.set_variants([
        {"part_number": "P", "ecu_type": "MG1", "event": "A"},
        {"part_number": "Q", "ecu_type": "MG2", "event": "B"},
    ])
    checklist._event_filter.setCurrentText("A")
    table = checklist._table
    assert set(checklist._checkboxes) == {"P"}
    assert table.item(0, 2).text() == "MG1"
    assert table.item(0, 3).text() == ""
    assert table.item(0, 4).text() == ""
    checklist.set_variants([])
    assert table.horizontalHeaderItem(0).text() == "Select"
    assert table.rowCount() == 0
    assert checklist._empty_label in checklist.findChildren(QLabel)
