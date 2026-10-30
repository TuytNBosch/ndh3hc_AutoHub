from PySide6.QtWidgets import QApplication, QComboBox, QStyledItemDelegate

from autohub.ui.combo_popup import install_combo_popup_style


def test_combo_gets_a_styled_delegate_once_shown():
    app = QApplication.instance() or QApplication([])
    keep = install_combo_popup_style(app)
    combo = QComboBox()
    combo.addItems(["a", "b"])
    combo.show()
    app.processEvents()
    assert type(combo.itemDelegate()) is QStyledItemDelegate
    assert keep is not None
