from selenium.webdriver.remote.webdriver import WebDriver

from .Actions import Actions
from .Information.Information import Information
from .JobCreation.JobCreation import JobCreation
from .Tab.Tab import Tab


class Body:
    """The page's main area: job creation form, action ribbon, job information and tabs."""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.job_creation = JobCreation(driver)
        self.actions = Actions(driver)
        self.information = Information(driver)
        self.tab = Tab(driver)
