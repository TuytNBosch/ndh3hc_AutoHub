"""Batch creation workflow, independent of Selenium and browser construction."""
from __future__ import annotations

import logging
from typing import Callable, Protocol

from autohub.core.progress import ProgressCallback, no_progress

from .step_log import run_step


class JobCreationPage(Protocol):
    def jobs_creation(
        self, ecu_generation: str, ecu_type: str, tool_version: str, routing: str,
        number_of_jobs: int, brand: str, customer_group: str, working_mode: str,
    ) -> bool: ...

    def get_new_jobs_ids(self) -> list[str]: ...


class JobBatch:
    def __init__(
        self, creation: JobCreationPage, open_dashboard: Callable[[], bool],
        open_creation: Callable[[], bool], open_job: Callable[[str], bool],
        fill_job: Callable[[dict], list[str]], job_url: Callable[[str], str],
        close: Callable[[], None], logger: logging.Logger,
    ):
        self.creation = creation
        self.open_dashboard = open_dashboard
        self.open_creation = open_creation
        self.open_job = open_job
        self.fill_job = fill_job
        self.job_url = job_url
        self.close = close
        self.logger = logger

    def run(
        self, variants: list, tool_version: str, routing: str,
        customer_group: str = "JAP", working_mode: str = "Honda_PreRun",
        progress: ProgressCallback = no_progress,
    ) -> list:
        if not variants:
            self.logger.info("No variants given, nothing to create")
            return []
        for variant in variants:
            missing = [key for key in ("ecu_generation", "brand", "ecu_type") if not variant.get(key)]
            if missing:
                raise ValueError(f"{variant['part_number']}: Master Sheet is missing required values: {', '.join(missing)}.")
        creation_values = {(v["ecu_generation"], v["brand"], v["ecu_type"]) for v in variants}
        if len(creation_values) != 1:
            raise ValueError("Selected variants must have the same Master Sheet ECU Generation, Brand and ECU Type.")
        first_variant = variants[0]
        brand = first_variant["brand"]
        self.logger.info(
            "WebFlow creation started: %d variant(s) %s, tool version %s, routing %s, brand %s, customer group %s, working mode %s",
            len(variants), [v["part_number"] for v in variants], tool_version, routing, brand, customer_group, working_mode,
        )
        progress("Opening the WebFlow dashboard...")
        if not run_step(self.logger, "Open the WebFlow dashboard", self.open_dashboard):
            raise RuntimeError("Could not open the WebFlow dashboard.")
        progress("Opening the new job page...")
        if not run_step(self.logger, "Open the new job page from the side menu", self.open_creation):
            raise RuntimeError("Could not open WebFlow job creation.")

        progress(f"Creating {len(variants)} job(s)...")
        self.logger.info("Creating %d job(s) for ECU %s / %s", len(variants), first_variant["ecu_generation"], first_variant["ecu_type"])
        created = self.creation.jobs_creation(
            ecu_generation=first_variant["ecu_generation"],
            ecu_type=first_variant["ecu_type"],
            tool_version=tool_version,
            routing=routing,
            number_of_jobs=len(variants),
            brand=brand,
            customer_group=customer_group,
            working_mode=working_mode,
        )
        if not created:
            raise RuntimeError("WebFlow job creation failed.")
        job_ids = self.creation.get_new_jobs_ids()
        self.logger.info("New job ids: %s", job_ids)
        if len(job_ids) != len(variants):
            raise RuntimeError("WebFlow returned an unexpected number of job IDs.")

        results = []
        for number, (job_id, variant) in enumerate(zip(job_ids, variants), start=1):
            progress(f"Filling job {job_id} for {variant['part_number']} ({number}/{len(variants)})...")
            self.logger.info("Job %s (%d/%d): filling variant %s", job_id, number, len(variants), variant["part_number"])
            if not run_step(self.logger, f"Open job {job_id}", self.open_job, job_id):
                raise RuntimeError(f"Could not open WebFlow job {job_id}.")
            warnings = self.fill_job(variant)
            self.logger.info("Job %s saved for variant %s: %s", job_id, variant["part_number"], self.job_url(job_id))
            result = {
                "PartNumber": variant["part_number"], "JobId": job_id, "Url": self.job_url(job_id),
            }
            if warnings:
                result["Warnings"] = warnings
            if variant.get("imported_software_part_number"):
                result["SoftwarePartNumber"] = variant["imported_software_part_number"]
            if variant.get("imported_ecr_number"):
                result["ECRNumber"] = variant["imported_ecr_number"]
            results.append(result)
        self.logger.info("WebFlow creation finished: %d job(s); closing the browser", len(results))
        self.close()
        return results
