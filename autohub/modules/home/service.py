"""Variant workflows over the Master Sheet / ECU Info Sheet / System Matrix (no Qt, no concrete I/O types)."""
from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Callable

from autohub.core.progress import ProgressCallback, no_progress
from autohub.core.ports import EcuInfoDocument, HWInfoDocument, KickOffDocument, SystemMatrixDocument, VariantSheet

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
        kick_off_factory: Callable[[str], KickOffDocument],
    ):
        self._master_sheet_factory = master_sheet_factory
        self._ecu_info_factory = ecu_info_factory
        self._system_matrix_factory = system_matrix_factory
        self._hw_info_factory = hw_info_factory
        self._session = session_factory
        self._kick_off_factory = kick_off_factory

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
        kick_off_path: str = "",
        progress: ProgressCallback = no_progress,
    ) -> list[dict]:
        with self._session():
            progress("Opening the source files...")
            system_matrix = self._system_matrix_factory(system_matrix_path)
            ecu_info_sheet = self._ecu_info_factory(ecu_info_path)
            master_sheet = self._master_sheet_factory(master_sheet_path)
            try:
                hw_info = None
                if hw_info_path:
                    progress("Reading HW info...")
                    hw_info = self._hw_info_factory(hw_info_path)
                    self._load(hw_info, "HW info")

                kick_off = None
                if kick_off_path:
                    progress("Reading the Kick Off Meeting...")
                    kick_off_document = self._kick_off_factory(kick_off_path)
                    self._load(kick_off_document, "Kick Off Meeting")
                    kick_off = kick_off_document.info

                progress("Reading the System Matrix...")
                system_matrix.open()
                self._load(system_matrix, "System Matrix data")

                progress("Reading the ECU Info Sheet...")
                ecu_info_sheet.open()
                self._load(ecu_info_sheet, "ECU Info Sheet data")

                progress("Opening the Master Sheet...")
                master_sheet.open()
                progress("Building the new variants...")
                return master_sheet.compute_new_variants(system_matrix.system_info, ecu_info_sheet.ecu_info, hw_info, kick_off)
            finally:
                master_sheet.close()
                ecu_info_sheet.close()
                system_matrix.close()

    def save_variants(
        self, master_sheet_path: str, variants: list[dict], progress: ProgressCallback = no_progress
    ) -> tuple[list, list[dict], list[dict]]:
        """Returns (saved, reloaded table rows, WebFlow-ready variants)."""
        with self._session():
            master_sheet = self._master_sheet_factory(master_sheet_path)
            try:
                progress("Opening the Master Sheet...")
                master_sheet.open()
                progress(f"Writing {len(variants)} variant(s)...")
                saved = master_sheet.save_variant_rows(variants)
                progress("Reloading the variants...")
                rows = master_sheet.load_variant_rows()
                available = master_sheet.load_webflow_variants()
                return saved, rows, available
            finally:
                master_sheet.close()

    def load_variants(
        self, master_sheet_path: str, progress: ProgressCallback = no_progress
    ) -> tuple[list[dict], list[dict]]:
        """Returns (table rows, WebFlow-ready variants)."""
        with self._session():
            master_sheet = self._master_sheet_factory(master_sheet_path)
            try:
                progress("Opening the Master Sheet...")
                master_sheet.open()
                progress("Reading the variants...")
                rows = master_sheet.load_variant_rows()
                available = master_sheet.load_webflow_variants()
                return rows, available
            finally:
                master_sheet.close()
