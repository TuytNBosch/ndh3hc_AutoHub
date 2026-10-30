"""WebFlow job creation with ownership of the browser session (no Qt)."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from contextlib import AbstractContextManager, nullcontext
from typing import Callable, Protocol

from autohub.core.ports import SheetSession, WebFlowLinkWriter
from autohub.core.progress import ProgressCallback, no_progress

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebFlowConfig:
    driver_path: str
    base_url: str
    tool_version: str
    routing: str
    trace_dir: str = ""  #: when set, the page of every step is recorded there


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
        return results

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
        self.shutdown()
        _logger.info("Starting the browser (base URL %s, tool version %s, routing %s)", config.base_url, config.tool_version, config.routing)
        progress("Starting the browser...")
        self._webflow = self._webflow_factory(
            driver_path=config.driver_path, base_url=config.base_url, trace_dir=config.trace_dir
        )
        return self._webflow.create_and_fill_jobs(
            variants, tool_version=config.tool_version, routing=config.routing, progress=progress
        )

    def shutdown(self) -> None:
        if self._webflow is None:
            return
        try:
            self._webflow.quit()
        except Exception:
            _logger.debug("The browser was already closed")
        self._webflow = None
