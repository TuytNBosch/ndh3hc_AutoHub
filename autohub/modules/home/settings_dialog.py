"""The Home settings dialog (how many of the latest variants Load shows)."""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QWidget


class HomeSettingsDialog(QDialog):
    def __init__(self, latest_count: int, choices: tuple[int, ...], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Home settings")
        self._latest = QComboBox()
        for count in choices:
            self._latest.addItem(str(count) if count else "All", count)
        self._latest.setCurrentIndex(max(0, self._latest.findData(latest_count)))
        self._latest.setToolTip("How many of the latest variants Load variants shows.")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form = QFormLayout(self)
        form.addRow("Latest variants:", self._latest)
        form.addRow(buttons)

    def latest_count(self) -> int:
        return self._latest.currentData()
