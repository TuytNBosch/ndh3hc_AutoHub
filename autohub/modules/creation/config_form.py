"""WebFlow connection settings: stored values and the dialog that edits them."""
from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPlainTextEdit, QWidget

from autohub.config import LOG_DIR
from autohub.core.settings import SettingsStore
from autohub.core.settings_keys import RECORD_PAGES_KEY
from autohub.modules.creation.service import WebFlowConfig

_DEFAULTS = {
    "webflow_base_url": "https://rb-pde-int.bosch.com:8881/app/dashboard",
    "tool_version": "PD W0002 (Productive)",
    "routing": "Honda_MG1CS022",
}


def _trace_dir() -> str:
    return str(LOG_DIR / "webflow_trace" / datetime.now().strftime("%Y%m%d_%H%M%S"))


def load_config(settings: SettingsStore) -> WebFlowConfig:
    saved = settings.load()
    return WebFlowConfig(
        driver_path="",
        base_url=str(saved.get("webflow_base_url", _DEFAULTS["webflow_base_url"])).strip(),
        tool_version=str(saved.get("tool_version", _DEFAULTS["tool_version"])).strip(),
        routing=str(saved.get("routing", _DEFAULTS["routing"])).strip(),
        trace_dir=_trace_dir() if saved.get(RECORD_PAGES_KEY, True) else "",
        change_engineer=str(saved.get("change_engineer", "")).strip(),
        cost_allocation=str(saved.get("cost_allocation", "")).strip(),
        change_reason=str(saved.get("change_reason", "")).strip(),
        ecr_notes=str(saved.get("ecr_notes", "")).strip(),
    )


class WebFlowSettingsDialog(QDialog):
    def __init__(self, config: WebFlowConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Creation settings")
        self.setMinimumWidth(460)
        self._base_url = QLineEdit(config.base_url)
        self._tool_version = QLineEdit(config.tool_version)
        self._routing = QLineEdit(config.routing)
        self._change_engineer = QLineEdit(config.change_engineer)
        self._cost_allocation = QLineEdit(config.cost_allocation)
        self._change_reason = QLineEdit(config.change_reason)
        self._change_reason.setPlaceholderText("Exact WebFlow options, separated by |")
        self._ecr_notes = QPlainTextEdit(config.ecr_notes)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form = QFormLayout(self)
        form.addRow("Base URL:", self._base_url)
        form.addRow("Tool version:", self._tool_version)
        form.addRow("Routing:", self._routing)
        form.addRow("Change engineer:", self._change_engineer)
        form.addRow("Cost allocation:", self._cost_allocation)
        form.addRow("Change Reason:", self._change_reason)
        form.addRow("ECR notes:", self._ecr_notes)
        form.addRow(buttons)

    def values(self) -> dict:
        return {
            "webflow_base_url": self._base_url.text().strip(),
            "tool_version": self._tool_version.text().strip(),
            "routing": self._routing.text().strip(),
            "change_engineer": self._change_engineer.text().strip(),
            "cost_allocation": self._cost_allocation.text().strip(),
            "change_reason": self._change_reason.text().strip(),
            "ecr_notes": self._ecr_notes.toPlainText().strip(),
        }
