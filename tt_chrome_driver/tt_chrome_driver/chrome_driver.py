from os import environ
from pathlib import Path

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger('selenium')
logger.setLevel(logging.DEBUG)
profile = environ['USERPROFILE']
handler = logging.FileHandler(Path(environ['USERPROFILE'] + '/Developer Workspace/log'))
logger.addHandler(handler)

def get_driver(download_dir=None):
    my_options = Options()
    if download_dir is not None:
        my_options.add_experimental_option("prefs", {'download.default_directory': str(download_dir)})
    driver = webdriver.Chrome(options=my_options)
    driver.implicitly_wait(10)  # seconds
    driver.minimize_window()
    return driver
