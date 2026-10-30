
import logging
import os
import time
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from autohub.core.progress import ProgressCallback, no_progress
from . import Constants as Constants
from .SideMenuBar import SideMenuBar
from .Body.Body import Body
from pathlib import Path

from .step_log import run_step, run_steps, set_step_observer
from .step_trace import StepTrace

_logger = logging.getLogger(__name__)


import requests
from requests import Response
from webdriver_manager.core.download_manager import WDMDownloadManager
from webdriver_manager.core.http import HttpClient

class CustomHttpClient(HttpClient):
    def get(self, url, params=None, **kwargs) -> Response:
        proxies = {
            'http': 'http://rb-proxy-apac.bosch.com:8080',
            'https': 'http://rb-proxy-apac.bosch.com:8080',
        }
        return requests.get(url, params, proxies=proxies, **kwargs)

class WebFlow(webdriver.Edge):

    def __init__(
        self,
        driver_path: str = "",
        base_url: str = "https://rb-pde-int.bosch.com:8881/app/dashboard",
        trace_dir: str = "",
    ):
        _logger.info("Starting the Edge browser (driver path: %s, base URL: %s)", driver_path or "auto", base_url)
        self.driver_path = driver_path
        self.base_url =base_url

        download_manager = WDMDownloadManager(CustomHttpClient())
        edge_options = Options()        
        service = Service(driver_path) if driver_path else Service(EdgeChromiumDriverManager(download_manager=download_manager).install())
        super(WebFlow, self).__init__(service=service, options=edge_options)
        self.implicitly_wait(Constants.IMPLICIT_WAIT)
        self.minimize_window()


        self.side_menu_bar = SideMenuBar(self)
        self.body = Body(self)
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

        WebDriverWait(self, Constants.BODY_TIMEOUT).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
        )

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
            WebDriverWait(self, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located(
                    (By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS)
                )
            )
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
            self._fill_job(variant)
            _logger.info("Job %s saved for variant %s: %s", job_id, variant["part_number"], self.job_url(job_id))
            results.append({
                "PartNumber": variant["part_number"],
                "JobId": job_id,
                "Url": self.job_url(job_id),
            })

        _logger.info("WebFlow creation finished: %d job(s); closing the browser", len(results))
        self.quit()  # only once every job is filled; quitting earlier broke the 2nd job onwards
        return results

    def _fill_job(self, variant: dict):
        part_number = variant["part_number"]
        general = self.body.tab.generaltab
        if not run_step(_logger, f"[{part_number}] Select the General tab", general.select_general_tab):
            raise RuntimeError("Could not select the General tab.")

        general_values = variant["general"]
        steps = [
            ("Close the side menu", self.side_menu_bar.close_menubar),
            ("Collapse the job information", self.body.information.collapse_job_information),
            ("General: delivery type", general.select_delivery_type, general_values["delivery_type"]),
            ("General: release class", general.select_release_class, general_values["release_class"]),
            ("General: release scope", general.select_release_scope, general_values["release_scope"]),
            ("General: limitations", general.select_limitations, general_values["limitations"]),
            ("General: safety monitoring SW", general.select_safety_monitoring_sw, general_values["safety_monitoring"]),
            ("General: safety calibration response", general.select_safety_calibration_response, general_values["safety_calibration"]),
            ("General: Bosch calibration data response", general.select_bosch_cal_data_response, general_values["calibration"]),
            ("General: data integration response", general.select_data_integration_response, general_values["data_integration"]),
        ]

        ecu_tab = self.body.tab.ecutab
        steps.append(("Select the ECU tab", ecu_tab.select_ecu_tab))
        ecu_values = variant["ecu"]
        for method, key in (
            (ecu_tab.fill_indi_spec, "indi_spec"),
            (ecu_tab.fill_family_name, "family_name"),
            (ecu_tab.fill_project_version, "project_version"),
            (ecu_tab.fill_program_version, "program_version")
        ):
            if ecu_values.get(key):
                steps.append((f"ECU: {key} = {ecu_values[key]}", method, ecu_values[key]))
        if ecu_values.get("tp_level"):
            steps.append((f"ECU: tp_level = {ecu_values['tp_level']}", ecu_tab.select_tp_level, ecu_values["tp_level"]))

        customer_tab = self.body.tab.customertab
        steps.append(("Select the Customer tab", customer_tab.select_customer_tab))
        customer_values = variant["customer"]
        for method, key in (
            (customer_tab.fill_ecu_default_id, "ecu_default_id"),
            (customer_tab.fill_ecu_program_id, "ecu_program_id"),
            (customer_tab.fill_ecu_rewriting_id, "ecu_rewriting_id"),
            (customer_tab.fill_security_coefficient, "security_coefficient"),
            (customer_tab.fill_sw_version, "sw_version"),
            (customer_tab.fill_component_id, "component_id")
        ):
            if customer_values.get(key):
                steps.append((f"Customer: {key} = {customer_values[key]}", method, customer_values[key]))

        steps.append(("Save the job", self.body.actions.save))
        failed = run_steps(_logger, [(f"[{part_number}] {step[0]}", *step[1:]) for step in steps])
        if failed:
            raise RuntimeError(f"Could not fill all values for {part_number}. Failed: {'; '.join(failed)}")
