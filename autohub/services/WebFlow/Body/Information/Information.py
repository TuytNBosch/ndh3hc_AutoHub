from selenium.webdriver.remote.webdriver import WebDriver

from ... import Constants as Constants
from ...components import Section


class Information:

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self._job_information = Section(
            driver, Constants.BODY_INFORMATION_TITLE_XPATH, Constants.BODY_INFORMATION_BODY_CSS, scroll=False
        )

    def is_job_information_expanded(self) -> bool:
        return self._job_information.is_expanded()

    # Unlike the tab sections, these report whether they clicked (False: nothing to do) and let a
    # missing header raise.
    def expand_job_information(self) -> bool:
        if self.is_job_information_expanded():
            return False
        self._job_information.toggle()
        return True

    def collapse_job_information(self) -> bool:
        if not self.is_job_information_expanded():
            return False
        self._job_information.toggle()
        return True
