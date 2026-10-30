import logging
import time


from ... import Constants as Constants
from ...dropdown import read_options


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


_logger = logging.getLogger(__name__)


def _checkbox_value(checkbox):
    """Return a checkbox's current value, including its indeterminate state."""
    value = checkbox.get_attribute("aria-checked")
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "mixed":
        return None

    try:
        checkbox.find_element(By.CSS_SELECTOR, 'checkicon[data-pc-section="checkIcon"]')
        return True
    except Exception:
        try:
            checkbox.find_element(By.CSS_SELECTOR, 'timesicon[data-pc-section="uncheckIcon"]')
            return False
        except Exception:
            return None


def _checkbox_is_disabled(form_element, checkbox_element) -> bool:
    """Recognize disabled states exposed by WebFlow's PrimeNG checkbox markup."""
    try:
        host = form_element.find_element(By.CSS_SELECTOR, "p-tristatecheckbox")
    except Exception:
        host = None

    for element in (host, checkbox_element):
        if element is None:
            continue
        if element.get_attribute("aria-disabled") == "true":
            return True
        if any(
            element.get_attribute(attribute) == "true"
            for attribute in ("ng-reflect-disabled", "ng-reflect-is-disabled")
        ):
            return True
        classes = element.get_attribute("class") or ""
        if any(name in classes.split() for name in ("bg-disabled", "p-checkbox-disabled", "p-disabled")):
            return True

    return False


def _click_count(current: bool | None, target: bool | None) -> int:
    """Number of tri-state cycles needed to reach a target value."""
    if current is target:
        return 0
    if target is None:
        return 2 if current is True else 1
    if current is None:
        return 1 if target else 2
    return 1


class GeneralTab:

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.skipped_fields: list[str] = []

    def is_general_tab(self) -> bool:
        
        try:
            tab_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.GENERAL_TAB_XPATH))
            )

            if not tab_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", tab_element)

            if not tab_element.is_selected():
                return False

        except:
            return False

        return True

    def select_general_tab(self) -> bool:

        if not self.is_general_tab():
            try:
                tab_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.GENERAL_TAB_XPATH))
                )

                if not tab_element.is_selected():
                    tab_element.click()
                    time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            except:
                return False

        return True




    def get_options(self) -> dict | None:
        return read_options(self.driver, Constants.GENERAL_TAB_OPTIONS_CLASS, Constants.GENERAL_TAB_OPTIONS_MAX_ITEMS)


    def is_configurator_items_expanded(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.GENERAL_CONFIGURATOR_ITEMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.GENERAL_CONFIGURATOR_ITEMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") != -1)
        except:
            return False
    
    def is_configurator_items_collapsed(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.GENERAL_CONFIGURATOR_ITEMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.GENERAL_CONFIGURATOR_ITEMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") == -1)
        except:
            return False

    def expand_configurator_items(self) -> bool:

        if not self.is_configurator_items_expanded():

            try:
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.GENERAL_CONFIGURATOR_ITEMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")

                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True

    def collapse_configurator_items(self) -> bool:

        if not self.is_configurator_items_collapsed():

            try: 
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.GENERAL_CONFIGURATOR_ITEMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")
                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True


    def select_delivery_type(self, delivery_type: str = "") -> bool:
        
        self.expand_configurator_items()

        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.GENERAL_DELIVERY_TYPE_TITLE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.GENERAL_TAB_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{delivery_type}"]')
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
            if options and delivery_type in options:
                options[delivery_type].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False


    
    def select_release_class(self, release_class: str = "") -> bool:
        
        self.expand_configurator_items()

        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.GENERAL_RELEASE_CLASS_TITLE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.GENERAL_TAB_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{release_class}"]')
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
            if options and release_class in options:
                options[release_class].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False


    def select_release_scope(self, release_scope: str = "") -> bool:
        
        self.expand_configurator_items()

        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.GENERAL_RELEASE_SCOPE_TITLE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.GENERAL_TAB_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{release_scope}"]')
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
            if options and release_scope in options:
                options[release_scope].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False


    def select_limitations(self, limitations: str = "") -> bool:
        
        self.expand_configurator_items()

        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.GENERAL_LIMITATIONS_TITLE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.GENERAL_TAB_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{limitations}"]')
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
            if options and limitations in options:
                options[limitations].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False

    def _select_tristate_checkbox(self, title_xpath: str, checkbox_css: str, check: bool | None, label: str) -> bool:
        if not self.expand_configurator_items():
            return False
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, title_xpath))
            )
            form_element = title_element.find_element(By.XPATH, "..")
            checkbox_element = form_element.find_element(By.CSS_SELECTOR, checkbox_css)
            current = _checkbox_value(checkbox_element)
            if current is check:
                return True

            if _checkbox_is_disabled(form_element, checkbox_element):
                warning = (
                    f"{label}: WebFlow disabled the control (current value {current!r}, "
                    f"requested {check!r}); the value was not changed."
                )
                self.skipped_fields.append(warning)
                _logger.warning(warning)
                return True

            for _ in range(_click_count(current, check)):
                checkbox_element.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                checkbox_element = form_element.find_element(By.CSS_SELECTOR, checkbox_css)
                current = _checkbox_value(checkbox_element)
                if current is check:
                    return True

            return current is check
        except Exception:
            _logger.exception("Could not set WebFlow checkbox %s", label)
            return False

    def select_safety_monitoring_sw(self, check: bool | None = None) -> bool:
        return self._select_tristate_checkbox(
            Constants.GENERAL_SAFETY_MONITORING_SW_BY_RB_TITLE_XPATH,
            Constants.GENERAL_SAFETY_MONITORING_SW_BY_RB_CHECKBOX_CSS,
            check,
            "Safety Monitoring SW by RB",
        )

    def select_safety_calibration_response(self, check: bool | None = None) -> bool:
        return self._select_tristate_checkbox(
            Constants.GENERAL_SAFETY_CALIBRATION_RESPONSIBILITY_TITLE_XPATH,
            Constants.GENERAL_SAFETY_CALIBRATION_RESPONSIBILITY_CHECKBOX_CSS,
            check,
            "Safety Calibration responsibility",
        )

    def select_bosch_cal_data_response(self, check: bool | None = None) -> bool:
        return self._select_tristate_checkbox(
            Constants.GENERAL_BOSCH_CAL_DATA_RESPONSIBILITY_TITLE_XPATH,
            Constants.GENERAL_BOSCH_CAL_DATA_RESPONSIBILITY_CHECKBOX_CSS,
            check,
            "Bosch calibration data responsibility",
        )

    def select_data_integration_response(self, check: bool | None = None) -> bool:
        return self._select_tristate_checkbox(
            Constants.GENERAL_DATA_INTEGRATION_RESPONSIBILITY_TITLE_XPATH,
            Constants.GENERAL_DATA_INTEGRATION_RESPONSIBILITY_CHECKBOX_CSS,
            check,
            "Data integration responsibility",
        )
