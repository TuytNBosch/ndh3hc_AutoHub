"""Settings page: the application theme (system / light / dark)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from autohub.core.settings import SettingsStore
from autohub.ui.theme import DEFAULT_THEME_MODE, apply_theme, normalize_theme_mode

THEME_KEY = "theme"
_LABELS = {"system": "System", "light": "Light", "dark": "Dark"}


class SettingsWidget(QWidget):
    def __init__(self, settings: SettingsStore):
        super().__init__()
        self._settings = settings

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")

        self._theme = QComboBox()
        for mode, label in _LABELS.items():
            self._theme.addItem(label, mode)
        saved = normalize_theme_mode(settings.load().get(THEME_KEY, DEFAULT_THEME_MODE))
        self._theme.setCurrentIndex(self._theme.findData(saved))
        self._theme.setToolTip("System follows the Windows light / dark setting.")

        form = QFormLayout()
        form.addRow("Theme:", self._theme)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addLayout(form)
        self._apply = QPushButton("Apply")
        self._apply.setToolTip("Save and apply the selected theme.")
        self._apply.clicked.connect(self._on_apply)
        layout.addWidget(self._apply, alignment=Qt.AlignLeft)

    def _on_apply(self) -> None:
        mode = self._theme.currentData()
        self._settings.update(**{THEME_KEY: mode})
        apply_theme(QApplication.instance(), mode)
