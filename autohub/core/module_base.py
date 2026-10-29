"""Base interface every AutoHub feature module must implement.

A module is a self-contained feature (e.g. FormB) that plugs into the
main window's sidebar without the shell needing to know its internals.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget


class AutoHubModule(ABC):
    """Contract for a pluggable feature module."""

    #: Short label shown in the sidebar.
    display_name: str = "Module"

    #: Icon file name under autohub/resources/icons/ (None falls back to a generic glyph).
    icon_file: str | None = None

    @abstractmethod
    def create_widget(self) -> QWidget:
        """Build and return the page widget shown when this module is selected."""
        raise NotImplementedError
