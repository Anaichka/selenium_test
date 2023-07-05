import os
import re
import time
import json
import logging
import requests


from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

result_permits = {}

def generate_pn() -> list:
    pn_list = []
    # Select range for generating permit list lenght
    for num in range(1, 5):
        pn_list.append(f"202201000{num}") if num < 10 else pn_list.append(f"20220100{num}")
    return pn_list

def parse_response_form(form_data, pn): 
    try:
        new_dict = {}
        new_dict['permit_number'] = pn
        new_dict['permit_status'] = form_data.find_element(By.ID, 'IWDBEDIT2').get_attribute('value')
        new_dict['type'] = form_data.find_element(By.ID, 'IWDBEDIT12').get_attribute('value')
        new_dict['type_detailed'] = form_data.find_element(By.ID, 'IWDBEDIT3').get_attribute('value')
        new_dict['owner'] = form_data.find_element(By.ID, 'IWDBEDIT4').get_attribute('value')
        new_dict['address'] = form_data.find_element(By.ID, 'IWDBEDIT5').get_attribute('value')
        new_dict['parcel'] = form_data.find_element(By.ID, 'IWDBEDIT14').get_attribute('value')
        new_dict['dba'] = form_data.find_element(By.ID, 'IWDBEDIT6').get_attribute('value')
        new_dict['job_desc'] = form_data.find_element(By.ID, 'IWDBMEMO1').get_attribute('value')
        new_dict['apply_date'] = form_data.find_element(By.ID, 'IWDBEDIT13').get_attribute('value')
        new_dict['issued_date'] = form_data.find_element(By.ID, 'IWDBEDIT8').get_attribute('value')
        new_dict['co_date'] = form_data.find_element(By.ID, 'IWDBEDIT7').get_attribute('value')
        new_dict['exp_date'] = form_data.find_element(By.ID, 'IWDBEDIT9').get_attribute('value')
        new_dict['last_insp_date'] = form_data.find_element(By.ID, 'IWDBEDIT10').get_attribute('value')
        new_dict['last_insp_result'] = form_data.find_element(By.ID, 'IWDBEDIT11').get_attribute('value')
        result_permits[pn] = new_dict
            
    except Exception as e:
        logging.error(pn, e)
            
def parse_add_info(add_info, pn):
    p_dict = result_permits.get(pn)
    p_dict['add_info'] = add_info[0].get_attribute('value')
    

def selenium_parse():

    logger = logging.getLogger('log-selenium-driver')

    start_url = "https://www.marionfl.org/agencies-departments/departments-facilities-offices/building-safety/permit-inspections"

    # Generates a list of PN
    permit_number_list = generate_pn()

    proxy = 'http://139.144.24.46:8080'

    session = requests.Session()
    response = session.get(start_url, proxies={'http': proxy})

    # It will be easier and quicker to find a direct page with submit form than wait for it to appear on a page
    link_to_navigate = re.findall(r'height="797" src="([^"]+)', response.text)[0]

    options = Options()
    # Disable options below if you  have a chromedriver and wanna run script locally
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--start-maximized')

    # end of options

    # Add proxy configuration
    options.add_argument('--proxy-server=http://139.144.24.46:8080')


    # And now we can initiate our driver
    driver = webdriver.Chrome(options=options)
    for pn in permit_number_list:
        logger.warning('Starting a process for Permit Number: {}'.format(pn))
        try:
            # Load the form page
            driver.get(link_to_navigate)
            time.sleep(3)
            button = driver.find_element(By.ID, "BTNPERMITS")
                
            # Click the button
            button.click()
            # Wait for the new element to appear
            wait = WebDriverWait(driver, 10)
            span_element = wait.until(EC.presence_of_element_located((By.ID, "EDTPERMITNBRDIV")))
        
            # Find the nested input element within the span element
            input_element = span_element.find_element(By.TAG_NAME, "input")


            # Type the permit number into the input field
            input_element.send_keys(pn)
            # Wait until continue button will be enabled
            button = wait.until(EC.element_to_be_clickable((By.ID, "BTNGUESTLOGIN")))
            button.click()
            returned_form = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='IWTABCONTROL1CSS-PAGE IWTABCONTROL1CSS-PAGE0']/form")))
            parse_response_form(returned_form, pn)
            time.sleep(2)
           
            add_info_button = driver.find_element(By.ID, "PAGETITLE_IWTABCONTROL1PAGE0")
            add_info_button.click()
            add_info = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//textarea[@id="IWDBMEMO2"]')))
            parse_add_info(add_info, pn)
            
            time.sleep(5)
        except NoSuchWindowException:
            logger.error('No information for this Permit Number!')
        except Exception as e:
            logger.error('Something went wrong, error occured: ', e)
    
    
    logger.warning('Task finished. You can find your JSON file in your main directory! Exiting...')


if __name__ == "__main__":
    selenium_parse()

    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
    with open(file_path, 'w') as fp:
        json.dump([result_permits], fp)
