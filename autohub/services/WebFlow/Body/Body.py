import time


from .. import Constants as Constants
from .JobCreation.JobCreation import JobCreation
from .Actions import Actions
from .Tab.Tab import Tab
from .Information.Information import Information

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class Body:

    def __init__(self, driver: WebDriver):
        self.driver = driver
        
        self.job_creation = JobCreation(driver)
        self.actions = Actions(driver)
        self.information = Information(driver)
        self.tab = Tab(driver)
        




    