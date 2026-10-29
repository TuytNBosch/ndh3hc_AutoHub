"""Variant workflows over the Master Sheet / ECU Info Sheet / System Matrix (no Qt, no concrete I/O types)."""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Callable

from autohub.core.ports import EcuInfoDocument, HWInfoDocument, SystemMatrixDocument, VariantSheet

#: Opens whatever per-thread resource the documents need (COM) around one operation.
SessionFactory = Callable[[], AbstractContextManager]


class VariantService:
    """Each method runs inside its own session, so it is safe to call from a worker thread."""

    def __init__(
        self,
        master_sheet_factory: Callable[[str], VariantSheet],
        ecu_info_factory: Callable[[str], EcuInfoDocument],
        system_matrix_factory: Callable[[str], SystemMatrixDocument],
        hw_info_factory: Callable[[str], HWInfoDocument],
        session_factory: SessionFactory,
    ):
        self._master_sheet_factory = master_sheet_factory
        self._ecu_info_factory = ecu_info_factory
        self._system_matrix_factory = system_matrix_factory
        self._hw_info_factory = hw_info_factory
        self._session = session_factory

    @staticmethod
    def _load(document, description: str) -> None:
        if not document.load_data():
            raise ValueError(getattr(document, "last_error", "") or f"Could not load {description}.")

    def compute_new_variants(
        self,
        master_sheet_path: str,
        ecu_info_path: str,
        system_matrix_path: str,
        hw_info_path: str = "",
    ) -> list[dict]:
        with self._session():
            system_matrix = self._system_matrix_factory(system_matrix_path)
            ecu_info_sheet = self._ecu_info_factory(ecu_info_path)
            master_sheet = self._master_sheet_factory(master_sheet_path)
            try:
                hw_info = None
                if hw_info_path:
                    hw_info = self._hw_info_factory(hw_info_path)
                    self._load(hw_info, "HW info")

                system_matrix.open()
                self._load(system_matrix, "System Matrix data")

                ecu_info_sheet.open()
                self._load(ecu_info_sheet, "ECU Info Sheet data")

                master_sheet.open()
                return master_sheet.compute_new_variants(system_matrix.system_info, ecu_info_sheet.ecu_info, hw_info)
            finally:
                master_sheet.close()
                ecu_info_sheet.close()
                system_matrix.close()

    def save_variants(self, master_sheet_path: str, variants: list[dict]) -> tuple[list, list[dict], list[dict]]:
        """Returns (saved, reloaded table rows, WebFlow-ready variants)."""
        with self._session():
            master_sheet = self._master_sheet_factory(master_sheet_path)
            try:
                master_sheet.open()
                saved = master_sheet.save_variant_rows(variants)
                rows = master_sheet.load_variant_rows()
                available = master_sheet.load_webflow_variants()
                return saved, rows, available
            finally:
                master_sheet.close()

    def load_variants(self, master_sheet_path: str) -> tuple[list[dict], list[dict]]:
        """Returns (table rows, WebFlow-ready variants)."""
        with self._session():
            master_sheet = self._master_sheet_factory(master_sheet_path)
            try:
                master_sheet.open()
                rows = master_sheet.load_variant_rows()
                available = master_sheet.load_webflow_variants()
                return rows, available
            finally:
                master_sheet.close()
