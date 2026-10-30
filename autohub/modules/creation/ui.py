"""Creation page: pick loaded variants and create/fill WebFlow jobs for them."""
from __future__ import annotations

import logging

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from autohub.core.dialogs import QtDialogs
from autohub.core.progress import ProgressWindow
from autohub.core.settings import SettingsStore
from autohub.core.workers import TaskRunner
from autohub.modules.creation.config_form import WebFlowSettingsDialog, load_config
from autohub.modules.creation.service import WebFlowJobService
from autohub.modules.creation.variant_checklist import VariantChecklist

_logger = logging.getLogger(__name__)


class CreationWidget(QWidget):
    def __init__(self, service: WebFlowJobService, settings: SettingsStore):
        super().__init__()

        self._service = service
        self._tasks = TaskRunner()

        title = QLabel("Create WebFlow jobs")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        subtitle = QLabel("Choose one or more variants loaded from the Master Sheet workflow.")
        subtitle.setStyleSheet("color: #888;")

        self._checklist = VariantChecklist(settings)
        self._settings = settings

        self._create_jobs_btn = QPushButton("Create WebFlow jobs")
        self._create_jobs_btn.setFixedWidth(190)
        self._create_jobs_btn.clicked.connect(self._create_webflow_jobs)
        self._settings_btn = QPushButton("Settings")
        self._settings_btn.setFixedWidth(120)
        self._settings_btn.clicked.connect(self._open_settings)
        create_jobs_row = QHBoxLayout()
        create_jobs_row.addWidget(self._settings_btn)
        create_jobs_row.addStretch(1)
        create_jobs_row.addWidget(self._create_jobs_btn)
        create_jobs_row.addStretch(1)

        self._webflow_status_label = QLabel("No variants loaded.")
        self._webflow_status_label.setStyleSheet("color: #888;")

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(self._checklist, stretch=1)
        layout.addSpacing(8)
        layout.addLayout(create_jobs_row)
        layout.addWidget(self._webflow_status_label)

    def set_variants(self, variants: list[dict]) -> None:
        """Populate the checklist with variants loaded/created on the Home page."""
        self._checklist.set_variants(variants)
        self._webflow_status_label.setText(
            "Select variants and create WebFlow jobs." if self._checklist.has_variants else "No variants loaded."
        )

    def _open_settings(self) -> None:
        dialog = WebFlowSettingsDialog(load_config(self._settings), self)
        if dialog.exec():
            self._settings.update(**dialog.values())

    def _create_webflow_jobs(self) -> None:
        selected = self._checklist.selected_variants()
        if not selected:
            QMessageBox.critical(self, "Create WebFlow jobs", "Select at least one variant.")
            return

        config = load_config(self._settings)
        if not config.tool_version or not config.routing:
            QMessageBox.critical(self, "Create WebFlow jobs", "Tool version and routing are required.")
            return

        if len({variant["ecu_type"] for variant in selected}) != 1:
            QMessageBox.critical(self, "Create WebFlow jobs", "Selected variants must use the same ECU type.")
            return

        _logger.info("Create WebFlow jobs clicked (%d variant(s), config=%s)", len(selected), config)
        self._create_jobs_btn.setEnabled(False)
        self._create_jobs_btn.setText("Creating jobs...")
        self._webflow_status_label.setText(f"Creating {len(selected)} WebFlow job(s)...")
        window = QtDialogs(self).open_progress("Create WebFlow jobs")
        self._tasks.start(
            lambda: self._service.create_jobs(selected, config, window.step),
            lambda results: self._finish_webflow_jobs(results, window),
            lambda error: self._fail_webflow_jobs(error, window),
        )

    def _finish_webflow_jobs(self, results: list[dict], window: ProgressWindow) -> None:
        self._create_jobs_btn.setEnabled(True)
        self._create_jobs_btn.setText("Create WebFlow jobs")
        self._webflow_status_label.setStyleSheet("color: #3fa66a;")
        self._webflow_status_label.setText(f"Created and filled {len(results)} WebFlow job(s).")
        _logger.info("Created %d WebFlow job(s)", len(results))
        summary = "\n".join(f"{item['PartNumber']}: {item['JobId']}" for item in results)
        window.succeed(f"Created and filled {len(results)} WebFlow job(s).\n{summary}")

    def _fail_webflow_jobs(self, error: str, window: ProgressWindow) -> None:
        self._create_jobs_btn.setEnabled(True)
        self._create_jobs_btn.setText("Create WebFlow jobs")
        self._webflow_status_label.setStyleSheet("color: #d9534f;")
        self._webflow_status_label.setText("WebFlow job creation failed.")
        _logger.error("Create WebFlow jobs failed: %s", error)
        window.fail(error)

    def shutdown(self) -> None:
        """Called by MainWindow on close so we don't leave a browser session running."""
        self._service.shutdown()
