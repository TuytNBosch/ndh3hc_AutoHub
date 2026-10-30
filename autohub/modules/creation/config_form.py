"""WebFlow connection settings: stored values and the dialog that edits them."""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QWidget

from autohub.core.settings import SettingsStore
from autohub.modules.creation.service import WebFlowConfig

_DEFAULTS = {
    "webflow_base_url": "https://rb-pde-int.bosch.com:8881/app/dashboard",
    "tool_version": "PD W0002 (Productive)",
    "routing": "Honda_MG1CS022",
}


def load_config(settings: SettingsStore) -> WebFlowConfig:
    saved = settings.load()
    return WebFlowConfig(
        driver_path="",
        base_url=str(saved.get("webflow_base_url", _DEFAULTS["webflow_base_url"])).strip(),
        tool_version=str(saved.get("tool_version", _DEFAULTS["tool_version"])).strip(),
        routing=str(saved.get("routing", _DEFAULTS["routing"])).strip(),
    )


class WebFlowSettingsDialog(QDialog):
    def __init__(self, config: WebFlowConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Creation settings")
        self.setMinimumWidth(460)
        self._base_url = QLineEdit(config.base_url)
        self._tool_version = QLineEdit(config.tool_version)
        self._routing = QLineEdit(config.routing)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form = QFormLayout(self)
        form.addRow("Base URL:", self._base_url)
        form.addRow("Tool version:", self._tool_version)
        form.addRow("Routing:", self._routing)
        form.addRow(buttons)

    def values(self) -> dict:
        return {
            "webflow_base_url": self._base_url.text().strip(),
            "tool_version": self._tool_version.text().strip(),
            "routing": self._routing.text().strip(),
        }
