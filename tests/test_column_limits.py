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


def test_settings_dialog_returns_the_chosen_latest_count():
    from PySide6.QtWidgets import QApplication
    from autohub.modules.home.presenter import LATEST_COUNT_CHOICES
    from autohub.modules.home.settings_dialog import HomeSettingsDialog
    QApplication.instance() or QApplication([])
    assert HomeSettingsDialog(20, LATEST_COUNT_CHOICES).latest_count() == 20
    assert HomeSettingsDialog(7, LATEST_COUNT_CHOICES).latest_count() == 5
