"""WebFlow job creation with ownership of the browser session (no Qt)."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from contextlib import AbstractContextManager, nullcontext
from typing import Callable, Protocol

from autohub.core.ports import SheetSession, WebFlowLinkWriter, WebFlowNumberWriter
from autohub.core.webflow_numbers import number_updates
from autohub.core.progress import ProgressCallback, no_progress

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebFlowConfig:
    driver_path: str
    base_url: str
    tool_version: str
    routing: str
    trace_dir: str = ""  #: when set, the page of every step is recorded there
    change_engineer: str = ""
    cost_allocation: str = ""
    change_reason: str = ""
    ecr_notes: str = ""


class WebFlowSession(Protocol):
    """The part of the WebFlow browser automation this service uses."""

    def create_and_fill_jobs(self, variants: list, tool_version: str, routing: str, progress: ProgressCallback = no_progress) -> list: ...

    def quit(self) -> None: ...


class WebFlowJobService:
    def __init__(
        self,
        webflow_factory: Callable[..., WebFlowSession],
        master_sheet_factory: Callable[[str], SheetSession] | None = None,
        session_factory: Callable[[], AbstractContextManager] = nullcontext,
    ):
        self._webflow_factory = webflow_factory
        self._master_sheet_factory = master_sheet_factory
        self._session = session_factory
        self._webflow: WebFlowSession | None = None
        self.last_elapsed_seconds = 0.0

    def create_jobs(
        self,
        variants: list[dict],
        config: WebFlowConfig,
        progress: ProgressCallback = no_progress,
        master_sheet_path: str = "",
    ) -> list[dict]:
        started = time.perf_counter()
        self.last_elapsed_seconds = 0.0
        completed = False
        try:
            results = self._create_jobs(variants, config, progress, master_sheet_path)
            completed = True
            return results
        finally:
            self.last_elapsed_seconds = time.perf_counter() - started
            _logger.info(
                "WebFlow jobs %s: %d requested; total time %.1f seconds (browser, filling, saving and link writing)",
                "completed" if completed else "failed", len(variants), self.last_elapsed_seconds,
            )

    def _create_jobs(
        self,
        variants: list[dict],
        config: WebFlowConfig,
        progress: ProgressCallback = no_progress,
        master_sheet_path: str = "",
    ) -> list[dict]:
        """Creates the jobs, then writes each job link into the Master Sheet (when a path is given).

        A failure to write the links is returned as "LinkError" on the results; the jobs exist either way."""
        _logger.info("Creating WebFlow jobs for %s", [v["part_number"] for v in variants])
        results = self._create(variants, config, progress)
        for item in results:
            _logger.info("Job %s created for %s: %s", item.get("JobId"), item.get("PartNumber"), item.get("Url"))
        if master_sheet_path:
            error = self._write_links(master_sheet_path, results, progress)
            if error:
                _logger.error("Writing the WebFlow links to the Master Sheet failed: %s", error)
                for item in results:
                    item["LinkError"] = error
            else:
                _logger.info("Wrote %d WebFlow link(s) to the Master Sheet", len(results))
        else:
            _logger.info("No Master Sheet path is set, so the links were not written")
        numbers = number_updates(results)
        if numbers:
            error = self._write_numbers(master_sheet_path, numbers, progress)
            if error:
                _logger.error("Writing WebFlow numbers failed: %s", error)
                for item in results:
                    item["NumberError"] = error
        return results

    def _write_numbers(self, path: str, numbers: dict[str, dict[str, str]], progress: ProgressCallback) -> str:
        if not path or self._master_sheet_factory is None:
            return "No Master Sheet path or writer is configured."
        try:
            with self._session():
                progress("Writing SW Part Number and ECR Number to the Master Sheet...")
                sheet = self._master_sheet_factory(path)
                try:
                    sheet.open()
                    if not isinstance(sheet, WebFlowNumberWriter):
                        return "This Master Sheet layout cannot write WebFlow numbers."
                    written = sheet.write_webflow_numbers(numbers)
                    if written != len(numbers):
                        return f"Only {written} of {len(numbers)} variants had their numbers written."
                finally:
                    sheet.close()
        except Exception as error:
            return str(error)
        return ""

    def _write_links(self, path: str, results: list[dict], progress: ProgressCallback) -> str:
        if self._master_sheet_factory is None:
            return ""
        links = {item["PartNumber"]: item["Url"] for item in results if item.get("Url")}
        try:
            with self._session():
                progress("Writing the WebFlow links to the Master Sheet...")
                sheet = self._master_sheet_factory(path)
                try:
                    sheet.open()
                    if not isinstance(sheet, WebFlowLinkWriter):
                        return "This Master Sheet layout has no WebFlow link column."
                    sheet.write_webflow_links(links)
                finally:
                    sheet.close()
        except Exception as error:
            return str(error)
        return ""

    def _create(self, variants: list[dict], config: WebFlowConfig, progress: ProgressCallback) -> list[dict]:
        ecr = {
            "change_engineer": config.change_engineer,
            "cost_allocation": config.cost_allocation,
            "change_reason": config.change_reason,
            "ecr_notes": config.ecr_notes,
        }
        if any(ecr.values()):
            missing = [key for key, value in ecr.items() if not value.strip()]
            if missing:
                raise ValueError(f"Complete ECR settings before creating jobs: {', '.join(missing)}.")
        job_variants = [{**variant, "ecr": dict(ecr)} for variant in variants] if any(ecr.values()) else variants
        for variant in variants:
            variant.pop("imported_ecr_number", None)
        self.shutdown()
        _logger.info("Starting the browser (base URL %s, tool version %s, routing %s)", config.base_url, config.tool_version, config.routing)
        progress("Starting the browser...")
        self._webflow = self._webflow_factory(
            driver_path=config.driver_path, base_url=config.base_url, trace_dir=config.trace_dir
        )
        try:
            results = self._webflow.create_and_fill_jobs(
                job_variants, tool_version=config.tool_version, routing=config.routing, progress=progress
            )
            # The batch has finished with the browser; release it now so app
            # close does not quit an already-stopped driver again.
            self.shutdown()
            return results
        finally:
            # Keep allocated numbers even if a later tab or job fails.
            for variant, job_variant in zip(variants, job_variants):
                if job_variant.get("imported_ecr_number"):
                    variant["imported_ecr_number"] = job_variant["imported_ecr_number"]

    def shutdown(self) -> None:
        if self._webflow is None:
            return
        try:
            self._webflow.quit()
        except Exception:
            _logger.debug("The browser was already closed")
        self._webflow = None
