"""Comparison page placeholder — implement the actual compare feature here."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from autohub.ui.theme import set_muted


class ComparisonWidget(QWidget):
    def __init__(self):
        super().__init__()

        title = QLabel("Comparison")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        subtitle = QLabel("Coming soon.")
        set_muted(subtitle, True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(title)
        layout.addWidget(subtitle)
