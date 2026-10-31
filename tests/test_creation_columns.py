from PySide6.QtCore import Qt
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
    assert [table.horizontalHeaderItem(col).text() for col in range(8)] == [
        "Select", "Part Number", "Family Name", "FSWID Project Version", "FSWID Program Version", "WebFlow Link",
        "SW Part Number", "ECR Number",
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
    checklist.set_numbers({"P": {"AX": "10SW001", "AW": "ECR123"}})
    assert [table.item(0, col).text() for col in (6, 7)] == ["10SW001", "ECR123"]
    checklist._apply_filter()
    assert table.item(0, 6).text() == "10SW001"


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


def test_event_is_left_aligned_and_extra_width_goes_to_part_number(qapp):
    checklist = VariantChecklist(MemorySettings())
    checklist.set_variants([{
        "part_number": "37820-6WZ-M610-M6", "ecu_type": "MG1CS022",
        "webflow_link": "https://webflow/app/ShowJob/16413",
        "ecu": {"project_version": "6WZX", "program_version": "V037"},
    }])
    checklist.resize(950, 300)
    checklist.show()
    qapp.processEvents()
    toolbar = checklist.layout().itemAt(0).layout()
    assert toolbar.itemAt(0).widget().text() == "Event:"
    assert toolbar.itemAt(1).widget() is checklist._event_filter
    header = checklist._table.horizontalHeader()
    assert not header.stretchLastSection()
    for width in (800, 950, 1100):
        checklist.resize(width, 300)
        qapp.processEvents()
        table = checklist._table
        assert len({table.columnWidth(col) for col in range(2, 6)}) == 1
        assert table.columnWidth(1) > table.columnWidth(2)
        assert table.columnWidth(1) > table.columnWidth(0)
        assert all(table.item(0, col).textAlignment() == Qt.AlignCenter for col in range(1, 5))
        assert table.cellWidget(0, 5).alignment() == Qt.AlignCenter
    checklist.close()
