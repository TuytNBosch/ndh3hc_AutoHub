"""Comparison page placeholder — implement the actual compare feature here."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ComparisonWidget(QWidget):
    def __init__(self):
        super().__init__()

        title = QLabel("Comparison")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")

        subtitle = QLabel("Coming soon.")
        subtitle.setStyleSheet("color: #888;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(title)
        layout.addWidget(subtitle)
