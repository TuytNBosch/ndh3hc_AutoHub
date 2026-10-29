import time


from . import Constants as Constants


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class SideMenuBar:

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def is_active(self) -> bool:
        """
        Checks if the side menu bar is active.

        Returns:
            bool: True if the side menu bar is active, False otherwise.
        """
        try:
            element = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, Constants.SIDEMENUBAR_ID))
            )
            return Constants.SIDEMENUBAR_ACTIVE in element.get_attribute("class")
        except:
            return False
     
    def open_menubar(self) -> bool:
        """
        Opens the side menu bar if it is not already active.

        Returns:
            bool: True if the side menu bar is active after the operation, False otherwise.
        """
        if not self.is_active():
            try:
                sidemenubar_element = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, Constants.SIDEMENUBAR_ID))
                )
    
                toggle_element = sidemenubar_element.find_element(By.XPATH, "..")

                button_element = toggle_element.find_element(By.CSS_SELECTOR, Constants.SIDEMENUBAR_OPEN_BTN_CSS)
                button_element.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            except:
                return False

        return True

    def close_menubar(self) -> bool:
        """
        Closes the side menu bar if it is currently active.

        Returns:
            bool: True if the side menu bar is inactive after the operation, False otherwise.
        """
        if self.is_active():
            try:
                sidemenubar_element = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, Constants.SIDEMENUBAR_ID))
                )

                button_element = sidemenubar_element.find_element(By.CSS_SELECTOR, Constants.SIDEMENUBAR_CLOSE_BTN_CSS)
                button_element.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
            except:
                return False

        return True
    

    def is_job_creation_expand(self) -> bool:
        """
        Checks if the job creation section in the side menu bar is expanded.

        Returns:
            bool: True if the job creation section is expanded, False otherwise.
        """
        try:
            job_creation_element = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, Constants.SIDEMENUBAR_JOBCREATION_CSS))
            )
            return "true" in job_creation_element.get_attribute("aria-expanded")
        except:
            return False

    def expand_job_creation(self) -> bool:
        """
        Expands the job creation section in the side menu bar if it is not already expanded.

        Returns:
            bool: True if the job creation section is expanded after the operation, False otherwise.
        """
        if not self.is_job_creation_expand():
            try:
                job_creation_element = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, Constants.SIDEMENUBAR_JOBCREATION_CSS))
                )

                toggle_button = job_creation_element.find_element(By.TAG_NAME, "button")

                toggle_button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                return self.is_job_creation_expand()
            except:
                return False
        return True

    def collapse_job_creation(self) -> bool:
        """
        Collapses the job creation section in the side menu bar if it is currently expanded.

        Returns:
            bool: True if the job creation section is collapsed after the operation, False otherwise.
        """
        if self.is_job_creation_expand():
            try:
                job_creation_element = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, Constants.SIDEMENUBAR_JOBCREATION_CSS))
                )
                toggle_button = job_creation_element.find_element(By.TAG_NAME, "button")
                toggle_button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                return not self.is_job_creation_expand()
            except:
                return False
        return True

    def click_new_job(self) -> bool:
        """
        Clicks the "New Job" button in the job creation section of the side menu bar.

        Returns:
            bool: True if the "New Job" button was successfully clicked, False otherwise.
        """
        try:
            if not self.is_job_creation_expand():
                self.expand_job_creation()

            new_job_button = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, Constants.SIDEMENUBAR_JOBCREATION_NEWJOB_BTN_CSS))
            )
            new_job_button.click()

            return WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False

    def click_new_job_from_xml(self) -> bool:
        """
        Clicks the "New Job from XML" button in the job creation section of the side menu bar.

        Returns:
            bool: True if the "New Job from XML" button was successfully clicked, False otherwise.
        """
        try:
            if not self.is_job_creation_expand():
                self.expand_job_creation()

            new_job_xml_button = WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, Constants.SIDEMENUBAR_JOBCREATION_NEWJOBXML_BTN_CSS))
            )
            new_job_xml_button.click()

            return WebDriverWait(self.driver, Constants.SIDEMENUBAR_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )
        except:
            return False

