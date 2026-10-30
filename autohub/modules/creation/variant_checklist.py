"""Variant checklist with event filter; persists the selection through a SettingsStore."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from autohub.core.settings import SettingsStore

_ALL_EVENTS = "All events"
_NO_EVENT = "(No event)"


class VariantChecklist(QWidget):
    def __init__(self, settings: SettingsStore):
        super().__init__()
        self._settings = settings
        # Only the latest variant per part number is kept by MasterSheet; this is the
        # full set, independent of whatever the event filter is currently showing.
        self._variants: list[dict] = []
        self._checkboxes: dict[str, QCheckBox] = {}
        self._selected: set[str] = set(settings.load().get("selected_variants", []))

        self._count_label = QLabel("Variants (0)")
        self._event_filter = QComboBox()
        self._event_filter.addItem(_ALL_EVENTS)
        self._event_filter.currentTextChanged.connect(self._apply_filter)
        select_all_btn = QPushButton("Select all")
        select_all_btn.clicked.connect(lambda: self._set_all(True))
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self._set_all(False))

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.addWidget(self._count_label, stretch=1)
        toolbar.addWidget(QLabel("Event:"))
        toolbar.addWidget(self._event_filter)
        toolbar.addWidget(select_all_btn)
        toolbar.addWidget(clear_btn)

        self._list_layout = QVBoxLayout()
        self._list_layout.setAlignment(Qt.AlignTop)
        self._empty_label = QLabel("Load variants from a Master Sheet on Home, or create them from all three files.")
        self._list_layout.addWidget(self._empty_label)

        container = QWidget()
        container.setLayout(self._list_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)
        scroll.setWidget(container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(toolbar)
        layout.addWidget(scroll)

    @property
    def has_variants(self) -> bool:
        return bool(self._variants)

    def selected_variants(self) -> list[dict]:
        return [v for v in self._variants if v["part_number"] in self._selected]

    def set_variants(self, variants: list[dict]) -> None:
        self._variants = variants

        events = sorted({v.get("event") or _NO_EVENT for v in variants})
        self._event_filter.blockSignals(True)
        current = self._event_filter.currentText() or _ALL_EVENTS
        self._event_filter.clear()
        self._event_filter.addItem(_ALL_EVENTS)
        self._event_filter.addItems(events)
        self._event_filter.setCurrentText(current if current in events or current == _ALL_EVENTS else _ALL_EVENTS)
        self._event_filter.blockSignals(False)

        self._apply_filter()

    def _apply_filter(self, *_args) -> None:
        self._checkboxes.clear()
        while self._list_layout.count():
            widget = self._list_layout.takeAt(0).widget()
            if widget is None:
                continue
            if widget is self._empty_label:
                # taking it out of the layout doesn't hide it; left visible it would
                # float over whatever gets added next.
                widget.hide()
            else:
                widget.deleteLater()

        event_filter = self._event_filter.currentText() or _ALL_EVENTS
        if event_filter == _ALL_EVENTS:
            filtered = self._variants
        else:
            filtered = [v for v in self._variants if (v.get("event") or _NO_EVENT) == event_filter]

        if not filtered:
            self._empty_label.show()
            self._list_layout.addWidget(self._empty_label)
        else:
            for variant in filtered:
                part_number = variant["part_number"]
                checkbox = QCheckBox(f"{part_number}    {variant['ecu_type']}")
                checkbox.setChecked(part_number in self._selected)
                checkbox.toggled.connect(lambda checked, pn=part_number: self._on_toggled(pn, checked))
                self._list_layout.addWidget(checkbox)
                self._checkboxes[part_number] = checkbox

        self._count_label.setText(f"Variants ({len(filtered)})")

    def _on_toggled(self, part_number: str, checked: bool) -> None:
        if checked:
            self._selected.add(part_number)
        else:
            self._selected.discard(part_number)
        self._settings.update(selected_variants=sorted(self._selected))

    def _set_all(self, checked: bool) -> None:
        for checkbox in self._checkboxes.values():
            checkbox.setChecked(checked)
