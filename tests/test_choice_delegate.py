import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QComboBox

from autohub.core.variant_choices import VARIANT_CHOICES
from autohub.core.variant_schema import VARIANT_FIELD_ORDER
from autohub.modules.home.choice_delegate import ChoiceDelegate


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_choice_columns_exist_in_the_table_schema():
    assert set(VARIANT_CHOICES) <= set(VARIANT_FIELD_ORDER)


def test_delegate_offers_the_list_and_keeps_unknown_values(app):
    from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

    table = QTableWidget(1, 1)
    table.setItem(0, 0, QTableWidgetItem("Legacy"))
    delegate = ChoiceDelegate(("Yes", "No"), table)
    index = table.model().index(0, 0)
    editor = delegate.createEditor(table, None, index)
    assert isinstance(editor, QComboBox)
    delegate.setEditorData(editor, index)
    assert [editor.itemText(i) for i in range(editor.count())] == ["", "Yes", "No", "Legacy"]
    editor.setCurrentText("No")
    delegate.setModelData(editor, table.model(), index)
    assert table.item(0, 0).text() == "No"
