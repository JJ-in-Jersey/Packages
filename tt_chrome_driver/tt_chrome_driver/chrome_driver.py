from os import environ

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logging.getLogger('WDM').setLevel(logging.NOTSET)

def get_driver(download_dir=None):
    my_options = Options()
    environ['WDM_LOG'] = "false"
    environ['WDM_LOG_LEVEL'] = '0'
    my_options.add_argument('disable-notifications')
    my_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if download_dir is not None:
        my_options.add_experimental_option("prefs", {'download.default_directory': str(download_dir)})
    driver = webdriver.Chrome(options=my_options)
    driver.implicitly_wait(10)  # seconds
    driver.minimize_window()
    return driver
