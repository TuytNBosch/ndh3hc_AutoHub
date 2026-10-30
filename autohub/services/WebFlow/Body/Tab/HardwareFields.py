"""Controls recorded in the General tab's Hardware/Plant information panel."""
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from autohub.core.webflow_fields import HARDWARE_FIELDS

from ... import Constants
from ...components import Section, pause, scroll_into_view_if_hidden, select_dropdown, wait_until_idle
from ...dropdown import read_options

_logger = logging.getLogger(__name__)
_FIELDS = {key: (label, kind) for _, key, label, kind in HARDWARE_FIELDS}


class HardwareFields:
    def __init__(self, driver):
        self.driver = driver
        self.section = Section(
            driver, '//span[normalize-space(.)="Hardware/Plant information"]', 'div[style^="display:"]'
        )

    def fill(self, key: str, value: str) -> bool:
        label, kind = _FIELDS[key]
        if not self.section.expand():
            return False
        title_xpath = f'.//div[contains(@class,"control-label") and normalize-space(.)="{label}"]'
        try:
            title = self.section.body().find_element(By.XPATH, title_xpath)
            form = title.find_element(By.XPATH, "..")
            if kind == "dropdown":
                return select_dropdown(
                    self.driver,
                    f'//div[contains(@class,"control-label") and normalize-space(.)="{label}"]',
                    Constants.GENERAL_TAB_BTN_CSS, value,
                    lambda: read_options(self.driver, Constants.GENERAL_TAB_OPTIONS_CLASS, Constants.GENERAL_TAB_OPTIONS_MAX_ITEMS),
                )
            if kind == "multi":
                return self._select_multiple(form, value)
            field = form.find_element(By.CSS_SELECTOR, 'input[type="text"]')
            scroll_into_view_if_hidden(self.driver, field)
            if not field.is_enabled() or field.get_attribute("readonly") is not None:
                _logger.error("WebFlow field %s is read-only; requested %r", label, value)
                return False
            field.clear()
            field.send_keys(value)
            pause()
            return field.get_attribute("value") == value
        except Exception:
            _logger.exception("Could not fill WebFlow field %s = %r", label, value)
            return False

    def _select_multiple(self, form, value: str) -> bool:
        control = form.find_element(By.CSS_SELECTOR, "p-multiselect")
        if control.get_attribute("ng-reflect-disabled") == "true":
            _logger.error("WebFlow multiselect is disabled; requested %r", value)
            return False
        control.find_element(By.CSS_SELECTOR, ".p-multiselect").click()
        try:
            panel = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                lambda driver: next(
                    (el for el in driver.find_elements(By.CSS_SELECTOR, ".p-multiselect-panel") if el.is_displayed()),
                    False,
                )
            )
            requested = {item.strip().casefold() for item in value.replace("\n", "|").split("|") if item.strip()}
            items = panel.find_elements(By.CSS_SELECTOR, "li.p-multiselect-item")
            options = {(item.get_attribute("aria-label") or item.text).strip().casefold(): item for item in items}
            if not requested.issubset(options):
                _logger.error("WebFlow multiselect does not offer %s", sorted(requested - options.keys()))
                return False
            for name, item in options.items():
                selected = item.get_attribute("aria-selected") == "true"
                if selected != (name in requested):
                    item.click()
            return all((item.get_attribute("aria-selected") == "true") == (name in requested) for name, item in options.items())
        finally:
            control.find_element(By.CSS_SELECTOR, ".p-multiselect").click()
            wait_until_idle(self.driver)
