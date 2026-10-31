"""Single-submit number import and its known save-before-import confirmation."""
import logging

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from . import Constants
from .components import Section

_logger = logging.getLogger(__name__)


class NumberImport:
    def __init__(self, driver: WebDriver, section: Section):
        self.driver = driver
        self.section = section

    def run(self, button_label: str, field_label: str) -> str:
        def available_button(_driver):
            button = self.section.body().find_element(
                By.XPATH, f'.//button[.//span[normalize-space(.)="{button_label}"]]'
            )
            return button if button.is_displayed() and button.is_enabled() else False

        button = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(available_button)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        # Allocating a number may have server-side effects: never retry the click.
        button.click()
        confirmed = False

        def imported(_driver):
            nonlocal confirmed
            for dialog in self.driver.find_elements(By.CSS_SELECTOR, '[role="dialog"], [role="alertdialog"]'):
                if not dialog.is_displayed():
                    continue
                if "Data filled in by you will be saved before import." not in dialog.text:
                    continue
                if not confirmed:
                    yes = dialog.find_element(
                        By.XPATH, './/button[normalize-space(.)="Yes" or .//span[normalize-space(.)="Yes"]]'
                    )
                    if not yes.is_displayed() or not yes.is_enabled():
                        return False
                    # Do not repeat confirmation after a stale DOM refresh.
                    confirmed = True
                    yes.click()
                    _logger.info("Confirmed saving changes before %s: Yes", button_label)
                return False
            field = self.section.body().find_element(
                By.XPATH,
                './/div[contains(@class,"form-group") and '
                f'./div[contains(@class,"control-label") and normalize-space(.)="{field_label}"]]//input',
            )
            value = (field.get_attribute("value") or "").strip()
            return value if value and value not in ("0", "---") else False

        return WebDriverWait(
            self.driver, Constants.WEBFLOW_TIMEOUT,
            ignored_exceptions=(StaleElementReferenceException,),
        ).until(imported)
