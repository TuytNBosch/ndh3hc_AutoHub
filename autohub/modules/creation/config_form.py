"""WebFlow connection settings form; each field persists itself on edit."""
from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QGridLayout, QLabel, QLineEdit, QPushButton, QWidget

from autohub.core.settings import SettingsStore
from autohub.modules.creation.service import WebFlowConfig

_DEFAULT_BASE_URL = "https://rb-pde-int.bosch.com:8881/app/dashboard"


class WebFlowConfigForm(QWidget):
    def __init__(self, settings: SettingsStore):
        super().__init__()
        self._settings = settings
        saved = settings.load()
        self._base_url_edit = self._make_edit(saved.get("webflow_base_url", _DEFAULT_BASE_URL), "webflow_base_url")
        self._tool_version_edit = self._make_edit(saved.get("tool_version", "PD W0002 (Productive)"), "tool_version")
        self._routing_edit = self._make_edit(saved.get("routing", "Honda_MG1CS022"), "routing")

        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(1, 1)
        rows = [
            ("Base URL", self._base_url_edit, None),
            ("Tool version", self._tool_version_edit, None),
            ("Routing", self._routing_edit, None),
        ]
        for row, (label_text, edit, extra) in enumerate(rows):
            label = QLabel(label_text)
            label.setFixedWidth(100)
            grid.addWidget(label, row, 0)
            grid.addWidget(edit, row, 1)
            if extra is not None:
                grid.addWidget(extra, row, 2)

    def config(self) -> WebFlowConfig:
        return WebFlowConfig(
            driver_path="",
            base_url=self._base_url_edit.text().strip(),
            tool_version=self._tool_version_edit.text().strip(),
            routing=self._routing_edit.text().strip(),
        )

    def _make_edit(self, value: str, settings_key: str) -> QLineEdit:
        edit = QLineEdit(value)
        edit.editingFinished.connect(lambda e=edit, key=settings_key: self._settings.update(**{key: e.text().strip()}))
        return edit

