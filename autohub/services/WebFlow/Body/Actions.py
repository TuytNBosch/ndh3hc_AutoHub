import time


from .. import Constants as Constants


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Actions:

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def get_button_by_text(self, text: str):
        try:
            action_ribbon = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, Constants.BODY_ACTION_RIBBON_CLASS))
            )

            if not action_ribbon.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", action_ribbon)

            buttons = action_ribbon.find_elements(By.TAG_NAME, "div")
            button_texts = action_ribbon.find_elements(By.TAG_NAME, "span")

            for button, title in zip(buttons, button_texts,):
                if title.text.strip().lower() == text.strip().lower():
                    return button

            return None
        except:
            return None

    def save(self) -> bool:
        button = self.get_button_by_text("save")

        if button is None:
            return False

        if button.get_attribute("class").find("disabled") != -1:
            return True

        button.click()

        return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

    def accept(self) -> bool:
        button = self.get_button_by_text("accept")

        if button is None:
            return False

        if button.get_attribute("class").find("disabled") != -1:
            return True

        button.click()

        return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )