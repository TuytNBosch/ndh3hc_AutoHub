"""Non-modal Find / Replace dialog driving a VariantTable."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FindReplaceDialog(QDialog):
    def __init__(self, table, parent: QWidget | None = None):
        super().__init__(parent)
        self._table = table
        self.setWindowTitle("Find")

        self._find_edit = QLineEdit()
        self._replace_edit = QLineEdit()
        self._match_case = QCheckBox("Match case")
        self._status = QLabel("")
        self._status.setStyleSheet("color: #888;")

        self._replace_label = QLabel("Replace with:")
        find_next_btn = QPushButton("Find next")
        find_next_btn.setDefault(True)
        self._replace_btn = QPushButton("Replace")
        self._replace_all_btn = QPushButton("Replace all")
        close_btn = QPushButton("Close")

        find_next_btn.clicked.connect(self._find_next)
        self._find_edit.returnPressed.connect(self._find_next)
        self._replace_btn.clicked.connect(self._replace)
        self._replace_all_btn.clicked.connect(self._replace_all)
        close_btn.clicked.connect(self.close)

        buttons = QHBoxLayout()
        buttons.addWidget(find_next_btn)
        buttons.addWidget(self._replace_btn)
        buttons.addWidget(self._replace_all_btn)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)

        grid = QGridLayout(self)
        grid.addWidget(QLabel("Find what:"), 0, 0)
        grid.addWidget(self._find_edit, 0, 1)
        grid.addWidget(self._replace_label, 1, 0)
        grid.addWidget(self._replace_edit, 1, 1)
        grid.addWidget(self._match_case, 2, 1)
        grid.addLayout(buttons, 3, 0, 1, 2)
        grid.addWidget(self._status, 4, 0, 1, 2)
        grid.setColumnMinimumWidth(1, 280)

    def open_for(self, replace: bool) -> None:
        self.setWindowTitle("Replace" if replace else "Find")
        for widget in (self._replace_label, self._replace_edit, self._replace_btn, self._replace_all_btn):
            widget.setVisible(replace)
        self._status.clear()
        self.show()
        self.raise_()
        self.activateWindow()
        self._find_edit.setFocus()
        self._find_edit.selectAll()

    def _find_next(self) -> None:
        text = self._find_edit.text()
        if not text:
            return
        found = self._table.find_next(text, self._match_case.isChecked())
        self._status.setText("" if found else "Not found.")

    def _replace(self) -> None:
        text = self._find_edit.text()
        if not text:
            return
        self._table.replace_current(text, self._replace_edit.text(), self._match_case.isChecked())
        self._find_next()

    def _replace_all(self) -> None:
        text = self._find_edit.text()
        if not text:
            return
        count = self._table.replace_all(text, self._replace_edit.text(), self._match_case.isChecked())
        self._status.setText(f"Replaced in {count} cell{'s' if count != 1 else ''}.")
