from unittest.mock import Mock

from PySide6.QtCore import Qt

from autohub.core.variant_schema import VARIANT_FIELD_ORDER
from autohub.modules.creation.ui import CreationWidget
from autohub.modules.home.ui import HomeWidget
from autohub.ui.main_window import MainWindow
from tests.fakes import MemorySettings


def test_created_links_reach_home_without_discarding_edits(qapp):
    settings = MemorySettings({"show_webflow_link": True})
    home = HomeWidget(Mock(), settings)
    creation = CreationWidget(Mock(), settings)
    MainWindow._wire_cross_module_signals([home, creation])
    rows = [
        {"_row": 11, "J": "P", "H": "edited", "_webflow_link": "https://webflow/app/ShowJob/1"},
        {"_row": 12, "J": "OTHER", "_webflow_link": "https://webflow/app/ShowJob/2"},
    ]
    home.show_rows(rows)
    home._presenter._loaded_rows = [dict(row) for row in rows]
    home._presenter.on_table_edited()
    home._presenter._deleted_rows = [13]
    home._variant_table.setRowHidden(0, True)
    edits = []
    home._variant_table.userEdited.connect(lambda: edits.append(True))
    link = "https://webflow/app/ShowJob/16409"

    creation._finish_webflow_jobs(
        [{"PartNumber": "P", "JobId": "16409", "Url": link, "LinkError": "Workbook locked"}],
        Mock(),
    )

    table = home._variant_table
    item = table.item(0, table._link_column)
    assert item.text() == "WF16409"
    assert item.data(Qt.UserRole) == link
    assert not item.flags() & Qt.ItemIsEditable
    assert table.isRowHidden(0)
    assert table.item(0, 1 + VARIANT_FIELD_ORDER.index("H")).text() == "edited"
    assert table.read()[0]["_webflow_link"] == link
    assert table.read()[1]["_webflow_link"].endswith("/2")
    assert home._presenter._loaded_rows[0]["_webflow_link"] == link
    assert home._presenter._deleted_rows == [13]
    assert home._update_btn.isEnabled()
    assert not edits
    home._presenter._show_rows(home._presenter._loaded_rows)
    assert table.item(0, table._link_column).text() == "WF16409"


def test_link_updates_preserve_hidden_column_and_ignore_unknown_parts(qapp):
    home = HomeWidget(Mock(), MemorySettings())
    home.show_rows([{"J": "P"}])
    home.set_webflow_links({"P": "https://webflow/app/ShowJob/3", "UNKNOWN": "unused"})

    table = home._variant_table
    assert table.rowCount() == 1
    assert table.isColumnHidden(table._link_column)
    assert table.item(0, table._link_column).text() == "WF3"
    assert not home._update_btn.isEnabled()
