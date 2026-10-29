"""Drop-down editor for table columns that webFLOW fills from a fixed list."""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QStyledItemDelegate


class ChoiceDelegate(QStyledItemDelegate):
    def __init__(self, choices: tuple[str, ...], parent=None):
        super().__init__(parent)
        self._choices = choices

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItem("")  # lets the user clear the cell
        editor.addItems(self._choices)
        editor.activated.connect(lambda _i, e=editor: self.commitData.emit(e))
        return editor

    def setEditorData(self, editor, index) -> None:
        text = str(index.data() or "")
        if text and editor.findText(text) < 0:
            editor.addItem(text)  # keep a value that is not in the list instead of losing it
        editor.setCurrentIndex(max(editor.findText(text), 0))

    def setModelData(self, editor, model, index) -> None:
        model.setData(index, editor.currentText())

    def updateEditorGeometry(self, editor, option, index) -> None:
        editor.setGeometry(option.rect)
