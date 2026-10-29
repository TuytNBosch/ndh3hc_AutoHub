import time


from ... import Constants as Constants


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class ECUTab:

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def is_ecu_tab(self) -> bool:
        
        try:
            tab_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_TAB_XPATH))
            )

            if not tab_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", tab_element)

            if not tab_element.is_selected():
                return False

        except:
            return False

        return True

    def select_ecu_tab(self) -> bool:

        if not self.is_ecu_tab():
            try:
                tab_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.ECU_TAB_XPATH))
                )

                if not tab_element.is_selected():
                    tab_element.click()
                    time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            except:
                return False

        return True



    def is_fsw_cnt_specific_parameters_expanded(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") != -1)
        except:
            return False
    
    def is_fsw_cnt_specific_parameters_collapsed(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") == -1)
        except:
            return False

    def expand_fsw_cnt_specific_parameters(self) -> bool:

        if not self.is_fsw_cnt_specific_parameters_expanded():

            try:
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")
                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True

    def collapse_fsw_cnt_specific_parameters(self) -> bool:

        if not self.is_fsw_cnt_specific_parameters_collapsed():

            try: 
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")
                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True

    def fill_indi_spec(self, data: str) -> bool:

        self.expand_fsw_cnt_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.ECU_INDI_SPEC_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True
    
    def fill_family_name(self, data: str) -> bool:

        self.expand_fsw_cnt_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.ECU_FAM_NAME_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True

    def fill_project_version(self, data: str) -> bool:

        self.expand_fsw_cnt_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSWID_PROJECT_VERSION_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True

    def fill_program_version(self, data: str) -> bool:

        self.expand_fsw_cnt_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_TITLE_XPATH))
            )
            info_element = title_element.find_element(By.XPATH, "../..")
            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSW_CNT_SPECIFIC_PARAMS_BODY_CSS)
            
            input_field = body_element.find_element(By.CSS_SELECTOR, Constants.ECU_FSWID_PROGRAM_VERSION_INPUT_CSS_SELECTOR)

            if not input_field.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", input_field)
                
            input_field.clear()
            input_field.send_keys(data)
            time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

        except:
            return False

        return True




    def is_ecu_specific_parameters_expanded(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_SPECIFIC_PARAMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_SPECIFIC_PARAMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") != -1)
        except:
            return False
    
    def is_ecu_specific_parameters_collapsed(self) -> bool:
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_SPECIFIC_PARAMS_TITLE_XPATH))
            )

            info_element = title_element.find_element(By.XPATH, "../..")

            body_element = info_element.find_element(By.CSS_SELECTOR, Constants.ECU_SPECIFIC_PARAMS_BODY_CSS)

            if not body_element.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView(true);", body_element)

            return (body_element.get_attribute("style").find("block") == -1)
        except:
            return False

    def expand_ecu_specific_parameters(self) -> bool:

        if not self.is_ecu_specific_parameters_expanded():

            try:
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.ECU_SPECIFIC_PARAMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")
                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True

    def collapse_ecu_specific_parameters(self) -> bool:

        if not self.is_ecu_specific_parameters_collapsed():

            try: 
                title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, Constants.ECU_SPECIFIC_PARAMS_TITLE_XPATH))
                )

                button = title_element.find_element(By.XPATH, "..")
                button.click()
                time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)  # Wait for the animation to complete

            except:
                return False

        return True

    def get_options(self) -> dict | None:

        options = {}
        has_options = False

        try:
            options_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, Constants.ECU_TAB_OPTIONS_CLASS))
            )

            default_element = options_element.find_element(By.TAG_NAME, "ul")
            item_id = default_element.get_attribute('id').replace('list','')

            for i in range(Constants.ECU_TAB_OPTIONS_MAX_ITEMS):
                item = WebDriverWait(self.driver, 1).until(EC.visibility_of_element_located((By.ID, item_id + str(i))))
                item_text = item.get_attribute('aria-label')
                options[item_text] = item

                if has_options is False:
                    has_options = True
        except:
            pass
        
        return options if has_options else None

    def select_tp_level(self, tp_level: str = "---") -> bool:
        self.expand_ecu_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_TP_LEVEL_TITLE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.ECU_TAB_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{tp_level}"]')
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
            if options and tp_level in options:
                options[tp_level].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False

    def select_diagnostic_protocol(self, diagnostic_protocol: str = "---") -> bool:
        self.expand_ecu_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_DIAGNOSTIC_PROTOCOL_TITLE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            button_element = form_element.find_element(By.CSS_SELECTOR, Constants.ECU_TAB_BTN_CSS)

            try:
                button_element.find_element(By.XPATH, f'.//span[text()="{diagnostic_protocol}"]')
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
            if options and diagnostic_protocol in options:
                options[diagnostic_protocol].click()

            return WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, Constants.WEBFLOW_ACTIVITY_INDICATOR_CLASS))
            )

        except:
            return False

    def select_project_lctvorb(self, check: bool = None) -> bool:
        self.expand_ecu_specific_parameters()
        try:
            title_element = WebDriverWait(self.driver, Constants.BODY_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, Constants.ECU_PROJECT_LCTVORB_TITLE_XPATH))
            )

            form_element = title_element.find_element(By.XPATH, "..")

            checkbox_element = form_element.find_element(By.CSS_SELECTOR, Constants.ECU_PROJECT_LCTVORB_CHECKBOX_CSS)
            
            ischecked = False
            isunchecked = False

            try:
                _= checkbox_element.find_element(By.CSS_SELECTOR, 'checkicon[data-pc-section="checkIcon"]')
                ischecked = True
            except:
                pass

            try:
                _= checkbox_element.find_element(By.CSS_SELECTOR, 'timesicon[data-pc-section="uncheckIcon"]')
                isunchecked = True
            except:
                pass

            if check is None:
                if not ischecked and not isunchecked:
                    return True
                elif ischecked:
                    checkbox_element.click()
                    time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                    checkbox_element.click()
                    time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                elif isunchecked:
                    checkbox_element.click()
                    time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                else:
                    return False

            else:
                if check: # True
                    if ischecked:
                        return True
                    elif isunchecked:
                        checkbox_element.click()
                        time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                        checkbox_element.click()
                        time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                    else:
                        checkbox_element.click()
                        time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

                else: # False
                    if isunchecked:
                        return True
                    elif ischecked:
                        checkbox_element.click()
                        time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                        
                    else:
                        checkbox_element.click()
                        time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)
                        checkbox_element.click()
                        time.sleep(Constants.WEBFLOW_TIMEOUT_CSS)

            return True

        except:
            return False