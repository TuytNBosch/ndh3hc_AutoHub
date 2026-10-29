"""VariantTable and the helpers split out of it: clipboard, search, frozen columns."""
import pytest
from PySide6.QtCore import QItemSelection, QItemSelectionModel
from PySide6.QtWidgets import QApplication

from autohub.core import normalizers as n
from autohub.core.variant_schema import VARIANT_FIELD_ORDER
from autohub.modules.home.variant_table import VariantTable

HEX_COLUMN = 1 + VARIANT_FIELD_ORDER.index("_hex")


@pytest.fixture
def table(qapp):
    widget = VariantTable()
    widget.resize(800, 300)
    widget.show()
    rows = [
        {"_row": 11 + i, **{c: f"{c}-{i}" for c in VARIANT_FIELD_ORDER if not c.startswith("_")}, "_hex": "AA"}
        for i in range(4)
    ]
    widget.populate(rows)
    qapp.processEvents()
    return widget


def _select(table, top, left, bottom, right):
    table.clearSelection()
    model = table.model()
    table.selectionModel().select(
        QItemSelection(model.index(top, left), model.index(bottom, right)), QItemSelectionModel.Select
    )


def test_read_returns_sheet_row_numbers_and_new_rows_without_one(table):
    assert [row["_row"] for row in table.read()] == [11, 12, 13, 14]
    table.populate([{"J": "new"}])
    assert table.read()[0]["_row"] is None and table.read()[0]["J"] == "new"


def test_clear_rows_forgets_the_row_numbers(table):
    table.clear_rows()
    assert table.rowCount() == 0 and table.read() == []


def test_float_cells_from_excel_show_as_integers(table):
    table.populate([{"AL": 159.0}])
    assert table.item(0, 1 + VARIANT_FIELD_ORDER.index("AL")).text() == "159"


def test_user_edits_emit_but_populate_does_not(table):
    edits = []
    table.userEdited.connect(lambda: edits.append(1))
    table.populate([{"J": "x"}])
    assert edits == []
    table.item(0, 1).setText("changed")
    assert edits == [1]


def test_copy_and_paste_roundtrip_a_block(table):
    _select(table, 0, 1, 1, 3)
    table.copy_selection()
    assert QApplication.clipboard().text() == "J-0\tH-0\tQ-0\nJ-1\tH-1\tQ-1"

    _select(table, 2, 1, 2, 1)
    assert table.paste_clipboard() == 6
    assert [table.item(3, c).text() for c in (1, 2, 3)] == ["J-1", "H-1", "Q-1"]


def test_pasting_one_value_fills_the_whole_selection(table):
    QApplication.clipboard().setText("ZZ")
    _select(table, 0, 2, 1, 3)
    assert table.paste_clipboard() == 4


def test_unchanged_writes_do_not_flag_an_edit(table):
    edits = []
    table.userEdited.connect(lambda: edits.append(1))
    QApplication.clipboard().setText("H-0")
    _select(table, 0, 2, 0, 2)
    assert table.paste_clipboard() == 0 and edits == []


def test_read_only_cells_are_never_changed(table):
    QApplication.clipboard().setText("NEW")
    _select(table, 0, HEX_COLUMN, 0, HEX_COLUMN)
    assert table.paste_clipboard() == 0
    assert table.delete_selection() == 0
    assert table.item(0, HEX_COLUMN).text() == "AA"
    _select(table, 0, 0, 0, 0)  # the "No." ordinal
    assert table.delete_selection() == 0


def test_delete_blanks_editable_cells(table):
    _select(table, 0, 1, 0, 2)
    assert table.delete_selection() == 2
    assert table.item(0, 1).text() == "" and table.item(0, 2).text() == ""


def test_find_wraps_skips_the_number_column_and_respects_case(table):
    table.setCurrentCell(0, 1)
    assert table.find_next("H-2") and (table.currentRow(), table.currentColumn()) == (2, 2)
    assert table.find_next("h-2", match_case=True) is False
    assert table.find_next("h-2", match_case=False) is True
    assert table.find_next("nothing-like-this") is False
    table.setCurrentCell(0, 1)
    assert table.find_next("1")  # "No." cells hold 1..4 but must never match
    assert table.currentColumn() != 0


def test_find_on_an_empty_table_finds_nothing(table):
    table.clear_rows()
    assert table.find_next("x") is False


def test_replace_current_and_replace_all_are_literal(table):
    table.setCurrentCell(0, 1)
    assert table.find_next("J-3") and table.replace_current("J-3", "X.*\\1")
    assert table.item(3, 1).text() == "X.*\\1"
    assert table.replace_current("not-there", "y") is False
    assert table.replace_all("-1", "+1") > 0
    assert table.replace_all("", "x") == 0


def test_frozen_columns_stay_put_when_scrolled_right(table):
    frozen = table._frozen
    before = frozen.view.geometry().getRect()
    bar = table.horizontalScrollBar()
    bar.setValue(bar.maximum())
    QApplication.processEvents()
    assert bar.maximum() > 0
    assert frozen.view.geometry().getRect() == before
    assert frozen.view.model().index(0, 1).data() == "J-0"
    assert frozen.is_frozen(1) and not frozen.is_frozen(2)


def test_context_menu_actions_exist_with_standard_shortcuts(table):
    shortcuts = {a.text(): a.shortcut().toString() for a in table.actions()}
    assert shortcuts == {
        "Copy": "Ctrl+C",
        "Paste": "Ctrl+V",
        "Delete": "Del",
        "Find...": "Ctrl+F",
        "Replace...": "Ctrl+H",
    }


def test_find_dialog_is_reused_and_hides_replace_for_find(table):
    table.show_find_dialog(True)
    dialog = table._find_dialog
    assert dialog.isVisible() and not dialog._replace_btn.isHidden()
    table.show_find_dialog(False)
    assert table._find_dialog is dialog and dialog._replace_btn.isHidden()
    dialog._find_edit.setText("nope-nope")
    dialog._find_next()
    assert dialog._status.text() == "Not found."
    dialog.close()


def test_normalize_key_text_collapses_whitespace_and_case():
    assert n.normalize_key_text("  62XS  for\nDAN/MP1 event ") == "62xs for dan/mp1 event"
