"""Sheet-backed controls in the General tab's collapsible panels."""
import logging

from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from autohub.core.webflow_fields import HARDWARE_FIELDS

from ... import Constants
from ...components import Section, pause, scroll_into_view_if_hidden, select_dropdown, wait_until_idle
from ...dropdown import read_options

_logger = logging.getLogger(__name__)
_FIELDS = {key: (label, kind) for _, key, label, kind in HARDWARE_FIELDS}
_PANEL_FIELDS = {
    "General info": (
        "vehicle_model", "engine_family", "power", "emission_norm", "immobilizer",
        "transmission", "displacement", "market", "model_year", "cylinders",
    ),
    "Bosch logistic info": (
        "project_number_first", "project_number_second", "hardware_part_number",
        "development_number", "ecu_hardware_name",
    ),
    "Customer logistic info": (
        "customer_order_number", "customer_hardware_part_number",
        "customer_software_part_number", "car", "customer_name",
    ),
    "Ident Numbers": ("lead_plant", "program_version", "software_part_number", "data_version"),
    "ECR Information": ("ecr_number",),
}
_FIELD_PANELS = {key: panel for panel, keys in _PANEL_FIELDS.items() for key in keys}


class HardwareFields:
    def __init__(self, driver):
        self.driver = driver
        self.sections = {
            panel: Section(driver, f'//span[normalize-space(.)="{panel}"]', 'div[style^="display:"]')
            for panel in _PANEL_FIELDS
        }

    def import_software_part_number(self) -> bool:
        section = self.sections["Ident Numbers"]
        if not section.expand():
            return False
        try:
            button_xpath = (
                '//button[.//span[normalize-space(.)="Import from pool"]]'
            )
            button = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, button_xpath))
            )
            scroll_into_view_if_hidden(self.driver, button)
            # Allocating a number may have server-side effects: never retry the click.
            button.click()
            wait_until_idle(self.driver, Constants.WEBFLOW_TIMEOUT)

            def imported(_driver):
                field = section.body().find_element(
                    By.XPATH,
                    './/div[contains(@class,"form-group") and '
                    './div[contains(@class,"control-label") and '
                    'normalize-space(.)="Software part number"]]//input',
                )
                value = (field.get_attribute("value") or "").strip()
                return value if value and value not in ("0", "---") else False

            value = WebDriverWait(
                self.driver, Constants.WEBFLOW_TIMEOUT,
                ignored_exceptions=(StaleElementReferenceException,),
            ).until(imported)
            _logger.info("WebFlow imported Software part number = %s", value)
            return True
        except Exception:
            _logger.exception("Could not import the software part number from pool")
            return False

    def fill(self, key: str, value: str) -> bool:
        label, kind = _FIELDS[key]
        section = self.sections[_FIELD_PANELS[key]]
        if not section.expand():
            return False
        title_xpath = f'.//div[contains(@class,"control-label") and normalize-space(.)="{label}"]'
        try:
            title = section.body().find_element(By.XPATH, title_xpath)
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
