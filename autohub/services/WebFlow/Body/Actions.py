import logging
import time


from .. import Constants as Constants
from ..toast import toast_severity


from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

_logger = logging.getLogger(__name__)


class Actions:

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def get_button_by_text(self, text: str):
        try:
            action_ribbon = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, Constants.BODY_ACTION_RIBBON_CLASS))
            )

            if not action_ribbon.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", action_ribbon)

            buttons = action_ribbon.find_elements(By.TAG_NAME, "div")
            button_texts = action_ribbon.find_elements(By.TAG_NAME, "span")

            for button, title in zip(buttons, button_texts,):
                if title.text.strip().lower() == text.strip().lower():
                    return button

            return None
        except:
            return None

    def save(self) -> bool:
        """Clicks Save and confirms WebFlow's "Saved successfully" toast; an error toast or no toast is a failure."""
        button = self.get_button_by_text("save")

        if button is None:
            return False

        if button.get_attribute("class").find("disabled") != -1:
            return True

        button.click()

        WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
        )
        return self._saved_toast_shown()

    def _saved_toast_shown(self) -> bool:
        def severity(driver):
            for toast in driver.find_elements(By.CSS_SELECTOR, Constants.TOAST_MESSAGE_CSS):
                found = toast_severity(toast.get_attribute("class"))
                if found in ("success", "error"):
                    return found, " ".join((toast.text or "").split())
            return False

        try:
            found, text = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(severity)
        except TimeoutException:
            _logger.error("WebFlow showed no confirmation after Save")
            return False
        if found == "error":
            _logger.error("WebFlow could not save: %s", text)
            return False
        _logger.info("WebFlow confirmed the save: %s", text)
        return True

    def accept(self) -> bool:
        button = self.get_button_by_text("accept")

        if button is None:
            return False

        if button.get_attribute("class").find("disabled") != -1:
            return True

        button.click()

        return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )