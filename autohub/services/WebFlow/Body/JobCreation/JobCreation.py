import logging
import time


from ... import Constants as Constants
from ...step_log import run_step
from autohub.core.webflow_links import job_number

_logger = logging.getLogger(__name__)


from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class JobCreation:

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.number_of_jobs = 0
        self.new_jobs_ids = []
    
    def is_job_creation_page(self) -> bool:
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, Constants.BODY_JOB_CREATION_PAGE_CLASS))
            )
            return True
        except:
            return False

    def get_number_of_jobs(self) -> int:
        return self.number_of_jobs

    def get_new_jobs_ids(self) -> list:
        return self.new_jobs_ids

    def confirm_button(self):
        try:
            confirm_button = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, Constants.BODY_JOBCREATION_CONFIRM_BTN_CSS))
            )
            
            return confirm_button
        except:
            return None

    def jobs_creation(self, ecu_generation: str, 
                           ecu_type: str , 
                           tool_version: str, 
                           routing: str, 
                           number_of_jobs: int,
                           brand: str = "Honda",
                           customer_group: str = "JAP", 
                           working_mode: str = "Honda_PreRun",) -> bool:
        success = True

        for label, value, select in (
            ("ECU generation", ecu_generation, self.select_ecu_generation),
            ("brand", brand, self.select_brand),
            ("ECU type", ecu_type, self.select_ecu_type),
            ("customer group", customer_group, self.select_customer_group),
            ("working mode", working_mode, self.select_working_mode),
            ("tool version", tool_version, self.select_tool_version),
            ("routing", routing, self.select_routing),
            ("number of jobs", number_of_jobs, self.select_number_of_jobs),
        ):
            if value:
                success &= run_step(_logger, f"Job creation form: select {label} = {value}", select, value)

        confirm = self.confirm_button()
        if confirm is not None:
            _logger.info("Step: confirm the job creation")
            confirm.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
        else:
            _logger.warning("The job creation confirm button was not found")

        success &= run_step(_logger, "Wait for WebFlow to finish creating the jobs", self._wait_until_jobs_created)

        if success:
            self.number_of_jobs = number_of_jobs

            current_url = self.driver.current_url
            current_id = job_number(current_url)

            for _ in range(number_of_jobs):
                self.new_jobs_ids.append(str(current_id))
                current_id += 1
            _logger.info("WebFlow created job id(s): %s (url %s)", ", ".join(self.new_jobs_ids), current_url)
        else:
            _logger.error("WebFlow job creation did not succeed")

        return success

    def _wait_until_jobs_created(self) -> bool:
        """Creating several jobs is slow: wait (up to WEBFLOW_TIMEOUT) for the spinner to go and the URL to end in the new job number."""
        def done(driver) -> bool:
            busy = driver.find_elements(By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS)
            return not any(element.is_displayed() for element in busy) and job_number(driver.current_url) is not None

        try:
            WebDriverWait(self.driver, Constants.WEBFLOW_TIMEOUT).until(done)
            return True
        except TimeoutException:
            _logger.error(
                "WebFlow did not finish creating the jobs within %ds (page: %s)", Constants.WEBFLOW_TIMEOUT, self.driver.current_url
            )
            return False

    def get_options(self) -> dict | None:

        options = {}
        has_options = False

        try:
            options_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, Constants.BODY_JOBCREATION_OPTIONS_CLASS))
            )

            default_element = options_element.find_element(By.TAG_NAME, "ul")
            item_id = default_element.get_attribute('id').replace('list','')

            for i in range(Constants.BODY_JOBCREATION_OPTIONS_MAX_ITEMS):
                item = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.ID, item_id + str(i))))
                item_text = item.get_attribute('aria-label')
                options[item_text] = item

                if has_options is False:
                    has_options = True
        except:
            pass
        
        return options if has_options else None

    def select_ecu_generation(self, ecu_generation: str = "---") -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_ECUGEN_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{ecu_generation}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False

            options = self.get_options()
            if options and ecu_generation in options:
                options[ecu_generation].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False

    def select_brand(self, brand: str = "---") -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_BRAND_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{brand}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False

            options = self.get_options()
            if options and brand in options:
                options[brand].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False

    def select_ecu_type(self, ecu_type: str = "---") -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_ECUTYPE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{ecu_type}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False

            options = self.get_options()
            if options and ecu_type in options:
                options[ecu_type].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False
    
    def select_customer_group(self, customer_group: str = "---") -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_CUSTGRP_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{customer_group}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False

            options = self.get_options()
            if options and customer_group in options:
                options[customer_group].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False

    def select_working_mode(self, working_mode: str = "---") -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_WRKMODE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{working_mode}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False    

            options = self.get_options()
            if options and working_mode in options:
                options[working_mode].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False

    def select_tool_version(self, tool_version: str = "---") -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_TOOLVER_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{tool_version}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False

            options = self.get_options()
            if options and tool_version in options:
                options[tool_version].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False
    
    def select_routing(self, routing: str = "---") -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_ROUTING_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{routing}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False

            options = self.get_options()
            if options and routing in options:
                options[routing].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False

    def select_number_of_jobs(self, number_of_jobs: int = 1) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_JOBCREATION_NUMBER_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.BODY_JOBCREATION_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{" " + str(number_of_jobs)}"]')
                return True
            except:
                pass

            button_element.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            is_displayed = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

            if not is_displayed:
                return False

            options = self.get_options()
            if options and " " + str(number_of_jobs) in options:
                options[" " + str(number_of_jobs)].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False