"""WebFlow browser session: opens the dashboard, creates jobs and fills them from variant dicts."""
import logging
import time
from pathlib import Path
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from autohub.core.progress import ProgressCallback, no_progress

from . import Constants as Constants
from .Body.Body import Body
from .browser import edge_service
from .components import wait_until_idle
from .job_filler import JobFiller
from .SideMenuBar import SideMenuBar
from .step_log import run_step, set_step_observer
from .step_trace import StepTrace

_logger = logging.getLogger(__name__)


class WebFlow(webdriver.Edge):

    def __init__(
        self,
        driver_path: str = "",
        base_url: str = "https://rb-pde-int.bosch.com:8881/app/dashboard",
        trace_dir: str = "",
    ):
        _logger.info("Starting the Edge browser (driver path: %s, base URL: %s)", driver_path or "auto", base_url)
        self.driver_path = driver_path
        self.base_url = base_url

        super().__init__(service=edge_service(driver_path), options=Options())
        self.implicitly_wait(Constants.IMPLICIT_WAIT)
        # self.minimize_window()

        self.side_menu_bar = SideMenuBar(self)
        self.body = Body(self)
        self.job_filler = JobFiller(self.side_menu_bar, self.body)
        _logger.info("Edge browser started")
        if trace_dir:  # record the page after every step
            set_step_observer(StepTrace(self, Path(trace_dir)))

    def quit(self):
        set_step_observer(None)
        super().quit()

    def __exit__(self, exc_type, exc_val, exc_tb):
        _logger.info("Closing the browser")
        self.quit()

    def open_dashboard_page(self) -> bool:

        _logger.info("Opening the WebFlow dashboard: %s", self.base_url)
        self.get(self.base_url)

        number_attempts = 0
        while self.title != Constants.WEBFLOW_TITLE and number_attempts < Constants.WEBFLOW_MAX_ATTEMPTS:
            self.refresh()
            time.sleep(Constants.WEBFLOW_REFRESH_INTERVAL)
            number_attempts += 1
            _logger.info("Dashboard not ready (title %r), refreshed (attempt %d/%d)", self.title, number_attempts, Constants.WEBFLOW_MAX_ATTEMPTS)

        if number_attempts >= Constants.WEBFLOW_MAX_ATTEMPTS:
            _logger.error("The WebFlow dashboard did not open after %d attempts", number_attempts)
            return False

        WebDriverWait(self, Constants.WEBFLOW_TIMEOUT).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_LOADING_SCREEN_CLASS))
        )

        wait_until_idle(self)

        _logger.info("The WebFlow dashboard is open")
        return True

    def job_url(self, job_id: str) -> str:
        url = urlsplit(self.base_url)
        return f"{url.scheme}://{url.netloc}/app/ShowJob/{job_id}"

    def open_job(self, job_id: str) -> bool:
        url = self.job_url(job_id)
        _logger.info("Opening job %s: %s", job_id, url)
        self.get(url)
        try:
            wait_until_idle(self)
            return True
        except Exception:
            _logger.exception("Job %s did not finish loading", job_id)
            return False

    def create_and_fill_jobs(
        self,
        variants: list,
        tool_version: str,
        routing: str,
        brand: str = "Honda",
        customer_group: str = "JAP",
        working_mode: str = "Honda_PreRun",
        progress: ProgressCallback = no_progress,
    ) -> list:
        if not variants:
            _logger.info("No variants given, nothing to create")
            return []
        for variant in variants:
            missing = [key for key in ("ecu_generation", "brand", "ecu_type") if not variant.get(key)]
            if missing:
                raise ValueError(f"{variant['part_number']}: Master Sheet is missing required values: {', '.join(missing)}.")
        creation_values = {(v["ecu_generation"], v["brand"], v["ecu_type"]) for v in variants}
        if len(creation_values) != 1:
            raise ValueError("Selected variants must have the same Master Sheet ECU Generation, Brand and ECU Type.")
        brand = variants[0]["brand"]
        _logger.info(
            "WebFlow creation started: %d variant(s) %s, tool version %s, routing %s, brand %s, customer group %s, working mode %s",
            len(variants), [v["part_number"] for v in variants], tool_version, routing, brand, customer_group, working_mode,
        )
        progress("Opening the WebFlow dashboard...")
        if not run_step(_logger, "Open the WebFlow dashboard", self.open_dashboard_page):
            raise RuntimeError("Could not open the WebFlow dashboard.")
        progress("Opening the new job page...")
        if not run_step(_logger, "Open the new job page from the side menu", self.side_menu_bar.click_new_job):
            raise RuntimeError("Could not open WebFlow job creation.")

        first_variant = variants[0]
        progress(f"Creating {len(variants)} job(s)...")
        _logger.info("Creating %d job(s) for ECU %s / %s", len(variants), first_variant["ecu_generation"], first_variant["ecu_type"])
        created = self.body.job_creation.jobs_creation(
            ecu_generation=first_variant["ecu_generation"],
            ecu_type=first_variant["ecu_type"],
            tool_version=tool_version,
            routing=routing,
            number_of_jobs=len(variants),
            brand=brand,
            customer_group=customer_group,
            working_mode=working_mode
        )
        if not created:
            raise RuntimeError("WebFlow job creation failed.")

        job_ids = self.body.job_creation.get_new_jobs_ids()
        _logger.info("New job ids: %s", job_ids)
        if len(job_ids) != len(variants):
            raise RuntimeError("WebFlow returned an unexpected number of job IDs.")

        results = []
        for number, (job_id, variant) in enumerate(zip(job_ids, variants), start=1):
            progress(f"Filling job {job_id} for {variant['part_number']} ({number}/{len(variants)})...")
            _logger.info("Job %s (%d/%d): filling variant %s", job_id, number, len(variants), variant["part_number"])
            if not run_step(_logger, f"Open job {job_id}", self.open_job, job_id):
                raise RuntimeError(f"Could not open WebFlow job {job_id}.")
            warnings = self._fill_job(variant)
            _logger.info("Job %s saved for variant %s: %s", job_id, variant["part_number"], self.job_url(job_id))
            result = {
                "PartNumber": variant["part_number"],
                "JobId": job_id,
                "Url": self.job_url(job_id),
            }
            if warnings:
                result["Warnings"] = warnings
            if variant.get("imported_software_part_number"):
                result["SoftwarePartNumber"] = variant["imported_software_part_number"]
            if variant.get("imported_ecr_number"):
                result["ECRNumber"] = variant["imported_ecr_number"]
            results.append(result)

        _logger.info("WebFlow creation finished: %d job(s); closing the browser", len(results))
        self.quit()  # only once every job is filled; quitting earlier broke the 2nd job onwards
        return results

    def _fill_job(self, variant: dict) -> list[str]:
        return self.job_filler.fill(variant)
