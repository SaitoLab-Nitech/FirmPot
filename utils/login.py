
#------------------------------------------------
# Import
#------------------------------------------------

import time

#------------------------------------------------
# Function
#------------------------------------------------

def login(driver, password, timer):

    # Input password
    form_list = []
    form_list = driver.find_elements_by_tag_name("input")

    if len(form_list) == 0:
        form_list = driver.find_elements_by_css_selector("input[type='password']")

    if len(form_list) > 0:

        for form in driver.find_elements_by_tag_name("input"):
            if len(form.get_attribute('value')) > 0: # the value is already in 
                continue
            try: 
                form.send_keys(password) # input password
            except:
                continue

    # Search submit buttons
    button_list = []

    button_list = driver.find_elements_by_tag_name("button")

    if len(button_list) == 0:
        button_list = driver.find_elements_by_css_selector("button[type='button']")

    if len(button_list) == 0:
        button_list = driver.find_elements_by_css_selector("input[type='submit']")

    if len(button_list) == 0:
        button_list = driver.find_elements_by_id("id_btn_login")

    # Click found buttons
    if len(button_list) > 0:
        for button in button_list:
            try: 
                button.click()
                break
            except:
                continue
    
    time.sleep(timer)



def first_login(ip_list, driver, password, timer):

    print("[*] Start First Login")
    
    for ip in ip_list:
        
        # Access to WebUI
        print("[*] Access to web server :", ip)
        driver.get(ip)
        time.sleep(timer)
        
        # Login Operation
        login(driver, password, timer)
