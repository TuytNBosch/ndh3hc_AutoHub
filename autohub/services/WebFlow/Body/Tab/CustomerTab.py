import time


from ... import Constants as Constants


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class CustomerTab:

    def __init__(self, driver: WebDriver):
        self.driver = driver


    def is_customer_tab(self) -> bool:
        
        try:
            tab_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_TAB_XPATH))
            )

            if not tab_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", tab_element)

            if not tab_element.is_selected():
                return False

        except:
            return False

        return True

    def select_customer_tab(self) -> bool:

        if not self.is_customer_tab():
            try:
                tab_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_TAB_XPATH))
                )

                if not tab_element.is_selected():
                    tab_element.click()
                    time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            except:
                return False

        return True

    def is_customer_specific_parameters_expanded(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") != -1)
        except:
            return False
    
    def is_customer_specific_parameters_collapsed(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") == -1)
        except:
            return False

    def expand_customer_specific_parameters(self) -> bool:

        if not self.is_customer_specific_parameters_expanded():

            try:
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")
                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True

    def collapse_customer_specific_parameters(self) -> bool:

        if not self.is_customer_specific_parameters_collapsed():

            try: 
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")
                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True

    def fill_ecu_default_id(self, data: str) -> bool:

        self.expand_customer_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_ECU_DEFAULT_ID_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True
    
    def fill_ecu_program_id(self, data: str) -> bool:

        self.expand_customer_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_ECU_PROGRAM_ID_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True
    
    def fill_ecu_rewriting_id(self, data: str) -> bool:

        self.expand_customer_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_ECU_REWRITING_ID_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True

    def fill_security_coefficient(self, data: str) -> bool:

        self.expand_customer_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SECURITY_COEFFICIENT_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True

    def fill_sw_version(self, data: str) -> bool:

        self.expand_customer_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SW_VERSION_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True

    def fill_component_id(self, data: str) -> bool:

        self.expand_customer_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.CUSTOMER_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.CUSTOMER_COMPONENT_ID_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True