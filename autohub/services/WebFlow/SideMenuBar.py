import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from . import Constants as Constants
from .components import pause, wait_for, wait_until_idle

_logger = logging.getLogger(__name__)


class SideMenuBar:

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def _menubar(self):
        return wait_for(self.driver, By.ID, Constants.SIDEMENUBAR_ID, Constants.SIDEMENUBAR_TIMEOUT)

    def _job_creation(self):
        return wait_for(self.driver, By.CSS_SELECTOR, Constants.SIDEMENUBAR_JOBCREATION_CSS, Constants.SIDEMENUBAR_TIMEOUT)

    def is_active(self) -> bool:
        """True if the side menu bar is open."""
        try:
            return Constants.SIDEMENUBAR_ACTIVE in self._menubar().get_attribute("class")
        except Exception:
            _logger.debug("Could not read the side menu bar", exc_info=True)
            return False

    def open_menubar(self) -> bool:
        """Opens the side menu bar; True if it is open afterwards."""
        if self.is_active():
            return True
        try:
            toggle_element = self._menubar().find_element(By.XPATH, "..")
            toggle_element.find_element(By.CSS_SELECTOR, Constants.SIDEMENUBAR_OPEN_BTN_CSS).click()
            pause()
            return True
        except Exception:
            _logger.warning("Could not open the side menu bar", exc_info=True)
            return False

    def close_menubar(self) -> bool:
        """Closes the side menu bar; True if it is closed afterwards."""
        if not self.is_active():
            return True
        try:
            self._menubar().find_element(By.CSS_SELECTOR, Constants.SIDEMENUBAR_CLOSE_BTN_CSS).click()
            pause()
            return True
        except Exception:
            _logger.warning("Could not close the side menu bar", exc_info=True)
            return False

    def is_job_creation_expand(self) -> bool:
        """True if the job creation section of the side menu bar is expanded."""
        try:
            return "true" in self._job_creation().get_attribute("aria-expanded")
        except Exception:
            _logger.debug("Could not read the job creation menu", exc_info=True)
            return False

    def _toggle_job_creation(self) -> None:
        self._job_creation().find_element(By.TAG_NAME, "button").click()
        pause()

    def expand_job_creation(self) -> bool:
        """Expands the job creation section; True if it is expanded afterwards."""
        if self.is_job_creation_expand():
            return True
        try:
            self._toggle_job_creation()
            return self.is_job_creation_expand()
        except Exception:
            _logger.warning("Could not expand the job creation menu", exc_info=True)
            return False

    def collapse_job_creation(self) -> bool:
        """Collapses the job creation section; True if it is collapsed afterwards."""
        if not self.is_job_creation_expand():
            return True
        try:
            self._toggle_job_creation()
            return not self.is_job_creation_expand()
        except Exception:
            _logger.warning("Could not collapse the job creation menu", exc_info=True)
            return False

    def _click_menu_item(self, item_css: str) -> bool:
        try:
            if not self.is_job_creation_expand():
                self.expand_job_creation()
            wait_for(self.driver, By.CSS_SELECTOR, item_css, Constants.SIDEMENUBAR_TIMEOUT).click()
            return wait_until_idle(self.driver, Constants.SIDEMENUBAR_TIMEOUT)
        except Exception:
            _logger.warning("Could not click side menu item %s", item_css, exc_info=True)
            return False

    def click_new_job(self) -> bool:
        """Clicks "New Job" and waits for the form; True on success."""
        return self._click_menu_item(Constants.SIDEMENUBAR_JOBCREATION_NEWJOB_BTN_CSS)

    def click_new_job_from_xml(self) -> bool:
        """Clicks "New Job from XML" and waits for the form; True on success."""
        return self._click_menu_item(Constants.SIDEMENUBAR_JOBCREATION_NEWJOBXML_BTN_CSS)
