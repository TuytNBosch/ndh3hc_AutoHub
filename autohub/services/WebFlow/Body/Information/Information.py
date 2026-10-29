import time


from ... import Constants as Constants


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Information:

    def __init__(self, driver: WebDriver):
        self.driver = driver


    def is_job_information_expanded(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_INFORMATION_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.BODY_INFORMATION_BODY_CSS)

            return (body_element.get_attribute("style").find("block") != -1)
        except:
            return False

    def expand_job_information(self):

        if not self.is_job_information_expanded():

            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_INFORMATION_TITLE_XPATH))
            )

            button = title_element.find_element(By.XPATH, "..")
            button.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            return True

        return False

    def collapse_job_information(self):

        if self.is_job_information_expanded():

            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.BODY_INFORMATION_TITLE_XPATH))
            )

            button = title_element.find_element(By.XPATH, "..")
            button.click()
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            return True

        return False