import logging
from os import environ

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.getLogger('WDM').setLevel(logging.NOTSET)

class ChromeDriver:

    @staticmethod
    def update_driver():
        my_options = Options()
        environ['WDM_LOG'] = "false"
        environ['WDM_LOG_LEVEL'] = '0'
        my_options.add_argument("--headless")
        my_options.add_argument('disable-notifications')
        my_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=my_options)
        driver.minimize_window()
        driver.close()

    @staticmethod
    def get_driver(download_dir=None):
        my_options = Options()
        environ['WDM_LOG'] = "false"
        environ['WDM_LOG_LEVEL'] = '0'
        my_options.add_argument('disable-notifications')
        my_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        if download_dir is not None:
            my_options.add_experimental_option("prefs", {'download.default_directory': str(download_dir)})
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=my_options)
        driver.implicitly_wait(30)  # seconds
        driver.minimize_window()
        return driver

    def __init__(self):
        pass
