"""Optional capabilities a page widget can advertise to the main window.

Small, separate interfaces (instead of one fat page base class) so a page only
implements what it actually needs.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VariantSource(Protocol):
    """Page that publishes variants; ``variantsLoaded`` is a Qt ``Signal(list)``."""

    variantsLoaded: Any


@runtime_checkable
class VariantSink(Protocol):
    """Page that consumes variants published by a ``VariantSource``."""

    def set_variants(self, variants: list[dict]) -> None: ...


@runtime_checkable
class Closable(Protocol):
    """Page that must release external resources when the app closes."""

    def shutdown(self) -> None: ...
