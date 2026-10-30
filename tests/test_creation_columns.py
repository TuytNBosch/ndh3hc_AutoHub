from PySide6.QtWidgets import QLabel

from autohub.modules.creation.variant_checklist import VariantChecklist
from tests.fakes import MemorySettings


def test_creation_headers_and_ecu_values(qapp):
    checklist = VariantChecklist(MemorySettings())
    checklist.set_variants([{
        "part_number": "P", "ecu_type": "MG1CS022",
        "ecu": {"family_name": "MG1CS022", "project_version": "6WZX", "program_version": "V037"},
    }])
    layout = checklist._list_layout
    assert [layout.itemAtPosition(0, col).widget().text() for col in range(5)] == [
        "Part Number", "Family Name", "FSWID Project Version", "FSWID Program Version", "WebFlow Link",
    ]
    assert [layout.itemAtPosition(1, col).widget().text() for col in range(4)] == [
        "P", "MG1CS022", "6WZX", "V037",
    ]
    checklist._checkboxes["P"].setChecked(True)
    checklist.set_links({"P": "https://webflow/app/ShowJob/42"})
    assert checklist._checkboxes["P"].isChecked()
    assert layout.itemAtPosition(1, 4).widget().text() == "WF42"
    assert layout.itemAtPosition(1, 2).widget().text() == "6WZX"


def test_missing_ecu_values_and_event_filter(qapp):
    checklist = VariantChecklist(MemorySettings())
    checklist.set_variants([
        {"part_number": "P", "ecu_type": "MG1", "event": "A"},
        {"part_number": "Q", "ecu_type": "MG2", "event": "B"},
    ])
    checklist._event_filter.setCurrentText("A")
    layout = checklist._list_layout
    assert set(checklist._checkboxes) == {"P"}
    assert layout.itemAtPosition(1, 1).widget().text() == "MG1"
    assert layout.itemAtPosition(1, 2).widget().text() == ""
    assert layout.itemAtPosition(1, 3).widget().text() == ""
    checklist.set_variants([])
    assert layout.itemAtPosition(0, 0).widget().text() == "Part Number"
    assert checklist._empty_label in checklist.findChildren(QLabel)
