from autohub.modules.home.column_limits import MAX_COLUMN_WIDTH, MIN_COLUMN_WIDTH, clamp_width
from autohub.modules.home.variant_table import VariantTable


def test_clamp_width():
    assert clamp_width(10) == MIN_COLUMN_WIDTH
    assert clamp_width(10_000) == MAX_COLUMN_WIDTH
    assert clamp_width(100) == 100


def test_columns_stay_within_limits(qtbot=None):
    from PySide6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    table = VariantTable()
    table.populate([{"J": "x" * 500}])
    for column in range(table.columnCount()):
        assert MIN_COLUMN_WIDTH <= table.columnWidth(column) <= MAX_COLUMN_WIDTH
    table.setColumnWidth(3, 5)
    assert table.columnWidth(3) == MIN_COLUMN_WIDTH
    table.setColumnWidth(3, 5000)
    assert table.columnWidth(3) == MAX_COLUMN_WIDTH
