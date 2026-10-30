"""Variant checklist with event filter; persists the selection through a SettingsStore."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from autohub.core.latest_event import NO_EVENT, latest_event
from autohub.core.webflow_links import webflow_link_text
from autohub.core.settings import SettingsStore
from autohub.ui.link_label import LinkLabel

_ALL_EVENTS = "All events"
_NO_EVENT = NO_EVENT
_HEADERS = (
    "Select", "Part Number", "Family Name", "FSWID Project Version", "FSWID Program Version", "WebFlow Link",
)


class VariantChecklist(QWidget):
    def __init__(self, settings: SettingsStore):
        super().__init__()
        self._settings = settings
        # Only the latest variant per part number is kept by MasterSheet; this is the
        # full set, independent of whatever the event filter is currently showing.
        self._variants: list[dict] = []
        self._checkboxes: dict[str, QCheckBox] = {}
        self._links: dict[str, str] = {}  # part number -> WebFlow job link
        self._selected: set[str] = set(settings.load().get("selected_variants", []))

        self._event_filter = QComboBox()
        self._event_filter.addItem(_ALL_EVENTS)
        self._event_filter.currentTextChanged.connect(self._apply_filter)
        self._event_filter.activated.connect(self._on_event_chosen)
        self._event_chosen = False  # once the user picks an event, reloads keep it
        select_all_btn = QPushButton("Select all")
        select_all_btn.clicked.connect(lambda: self._set_all(True))
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self._set_all(False))

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.addStretch(1)
        toolbar.addWidget(QLabel("Event:"))
        toolbar.addWidget(self._event_filter)
        toolbar.addWidget(select_all_btn)
        toolbar.addWidget(clear_btn)

        self._table = QTableWidget(0, len(_HEADERS))
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.setShowGrid(True)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setMinimumHeight(150)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._empty_label = QLabel("Load variants from a Master Sheet on Home, or create them from all three files.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(toolbar)
        layout.addWidget(self._table)
        layout.addWidget(self._empty_label)

    @property
    def has_variants(self) -> bool:
        return bool(self._variants)

    def selected_variants(self) -> list[dict]:
        return [v for v in self._variants if v["part_number"] in self._selected]

    def has_link(self, part_number: str) -> bool:
        return bool(self._links.get(part_number))

    def set_variants(self, variants: list[dict]) -> None:
        self._variants = variants
        for variant in variants:
            if variant.get("webflow_link"):
                self._links[variant["part_number"]] = variant["webflow_link"]

        events = sorted({v.get("event") or _NO_EVENT for v in variants})
        self._event_filter.blockSignals(True)
        current = self._event_filter.currentText() if self._event_chosen else (latest_event(variants) or _ALL_EVENTS)
        self._event_filter.clear()
        self._event_filter.addItem(_ALL_EVENTS)
        self._event_filter.addItems(events)
        self._event_filter.setCurrentText(current if current in events or current == _ALL_EVENTS else _ALL_EVENTS)
        self._event_filter.blockSignals(False)

        self._apply_filter()

    def _on_event_chosen(self, _index: int) -> None:
        self._event_chosen = True

    def _apply_filter(self, *_args) -> None:
        self._checkboxes.clear()
        self._table.setRowCount(0)

        event_filter = self._event_filter.currentText() or _ALL_EVENTS
        if event_filter == _ALL_EVENTS:
            filtered = self._variants
        else:
            filtered = [v for v in self._variants if (v.get("event") or _NO_EVENT) == event_filter]

        self._empty_label.setVisible(not filtered)
        self._table.setRowCount(len(filtered))
        if filtered:
            for row, variant in enumerate(filtered):
                part_number = variant["part_number"]
                checkbox = QCheckBox()
                checkbox.setAccessibleName(f"Select {part_number}")
                checkbox.setChecked(part_number in self._selected)
                checkbox.toggled.connect(lambda checked, pn=part_number: self._on_toggled(pn, checked))
                self._checkboxes[part_number] = checkbox
                container = QWidget()
                layout = QHBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(checkbox, alignment=Qt.AlignCenter)
                self._table.setCellWidget(row, 0, container)
                ecu = variant.get("ecu", {})
                for column, value in enumerate((
                    part_number,
                    ecu.get("family_name") or variant["ecu_type"],
                    ecu.get("project_version", ""),
                    ecu.get("program_version", ""),
                ), start=1):
                    self._table.setItem(row, column, QTableWidgetItem(str(value or "")))
                link = self._links.get(part_number, "")
                if link:
                    self._table.setCellWidget(
                        row, 5, LinkLabel(webflow_link_text(link) or link, link)
                    )

    def set_links(self, links: dict[str, str]) -> None:
        """Shows the WebFlow job link of the variants that just got a job."""
        self._links.update(links)
        self._apply_filter()

    def _on_toggled(self, part_number: str, checked: bool) -> None:
        if checked:
            self._selected.add(part_number)
        else:
            self._selected.discard(part_number)
        self._settings.update(selected_variants=sorted(self._selected))

    def _set_all(self, checked: bool) -> None:
        for checkbox in self._checkboxes.values():
            checkbox.setChecked(checked)
