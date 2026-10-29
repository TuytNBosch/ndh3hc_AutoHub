"""Narrow interfaces the services layer implements and the feature modules depend on.

Each protocol lists only what one client needs, so a fake can stand in for Excel in tests.
"""
from __future__ import annotations

from typing import Any, Protocol

from autohub.core.records import DocumentReader, EcuInfoData, HWLookup, SystemMatrixData


class SheetSession(Protocol):
    """Something that holds an external resource (an Excel instance) between open and close."""

    def open(self) -> None: ...

    def close(self) -> None: ...


class VariantReader(Protocol):
    def load_variant_rows(self) -> list[dict]: ...

    def load_webflow_variants(self) -> list[dict]: ...


class VariantWriter(Protocol):
    def save_variant_rows(self, variants: list[dict], save: bool = True) -> list[dict]: ...


class NewVariantSource(Protocol):
    def compute_new_variants(
        self, system_info: SystemMatrixData, ecu_info: EcuInfoData, hw_info: HWLookup | None = None
    ) -> list[dict]: ...


class VariantSheet(SheetSession, VariantReader, VariantWriter, NewVariantSource, Protocol):
    """The full Master Sheet session; services annotate narrower views of it where they can."""


class EcuInfoDocument(DocumentReader, SheetSession, Protocol):
    ecu_info: EcuInfoData


class SystemMatrixDocument(DocumentReader, SheetSession, Protocol):
    system_info: SystemMatrixData


class HWInfoDocument(DocumentReader, HWLookup, Protocol):
    records: list[dict[str, Any]]
