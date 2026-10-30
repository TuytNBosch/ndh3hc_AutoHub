from selenium.webdriver.remote.webdriver import WebDriver

from ... import Constants as Constants
from ...components import Section, TabLink


class CustomerTab:

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self._tab = TabLink(driver, Constants.CUSTOMER_TAB_XPATH)
        self._customer_parameters = Section(
            driver, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS
        )

    def is_customer_tab(self) -> bool:
        return self._tab.is_selected()

    def select_customer_tab(self) -> bool:
        return self._tab.select()

    def is_customer_specific_parameters_expanded(self) -> bool:
        return self._customer_parameters.is_expanded()

    def is_customer_specific_parameters_collapsed(self) -> bool:
        return self._customer_parameters.is_collapsed()

    def expand_customer_specific_parameters(self) -> bool:
        return self._customer_parameters.expand()

    def collapse_customer_specific_parameters(self) -> bool:
        return self._customer_parameters.collapse()

    def fill_ecu_default_id(self, data: str) -> bool:
        return self._customer_parameters.fill_input(Constants.CUSTOMER_ECU_DEFAULT_ID_INPUT_CSS_SELECTOR, data)

    def fill_ecu_program_id(self, data: str) -> bool:
        return self._customer_parameters.fill_input(Constants.CUSTOMER_ECU_PROGRAM_ID_INPUT_CSS_SELECTOR, data)

    def fill_ecu_rewriting_id(self, data: str) -> bool:
        return self._customer_parameters.fill_input(Constants.CUSTOMER_ECU_REWRITING_ID_INPUT_CSS_SELECTOR, data)

    def fill_security_coefficient(self, data: str) -> bool:
        return self._customer_parameters.fill_input(Constants.CUSTOMER_SECURITY_COEFFICIENT_INPUT_CSS_SELECTOR, data)

    def fill_sw_version(self, data: str) -> bool:
        return self._customer_parameters.fill_input(Constants.CUSTOMER_SW_VERSION_INPUT_CSS_SELECTOR, data)

    def fill_component_id(self, data: str) -> bool:
        return self._customer_parameters.fill_input(Constants.CUSTOMER_COMPONENT_ID_INPUT_CSS_SELECTOR, data)
