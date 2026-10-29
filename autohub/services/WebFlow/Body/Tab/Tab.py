import time


from ... import Constants as Constants
from .ECUTab import ECUTab
from .CustomerTab import CustomerTab
from .GeneralTab import GeneralTab

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Tab:

    def __init__(self, driver: WebDriver):
        self.driver = driver

        self.generaltab = GeneralTab(self.driver)
        self.ecutab = ECUTab(self.driver)
        self.customertab = CustomerTab(self.driver)