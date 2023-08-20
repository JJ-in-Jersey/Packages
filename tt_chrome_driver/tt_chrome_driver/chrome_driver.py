from pathlib import Path
from os import listdir
import re
import platform
import requests
from bs4 import BeautifulSoup as soup
from distutils.version import LooseVersion

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from tt_os_abstraction.os_abstraction import temp

logger = logging.getLogger('selenium')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(Path(temp() + '/logfile.tmp'))
logger.addHandler(handler)


def get_driver(download_dir=None):
    print(f'is_chrome_installed: {is_chrome_installed()}')
    print(f'get_installed_chrome_version: {get_installed_chrome_version()}')
    get_latest_chrome_version()
    my_options = Options()
    if download_dir is not None:
        my_options.add_experimental_option("prefs", {'download.default_directory': str(download_dir)})
    driver = webdriver.Chrome(options=my_options)
    driver.implicitly_wait(10)  # seconds
    driver.minimize_window()
    return driver


def is_chrome_installed():
    apple_exe_path = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    windows_exe_path = Path('C:/Program Files/Google/Chrome/Application/Chrome.exe')

    if platform.system() == 'Darwin':
        return apple_exe_path.exists()
    elif platform.system() == 'Windows':
        return windows_exe_path.exists()


def get_installed_chrome_version():
    apple_version_path = Path('/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions')
    windows_version_path = Path('C:/Program Files/Google/Chrome/Application')
    regex_pattern = '^[0-9\.]*$'
    file_list = None

    if platform.system() == 'Darwin':
        file_list = [s for s in listdir(apple_version_path) if re.search(regex_pattern, s) is not None]
    elif platform.system() == 'Windows':
        file_list = [s for s in listdir(windows_version_path) if re.search(regex_pattern, s) is not None]

    file_list.sort(key=LooseVersion)

    return file_list[-1]


def get_latest_chrome_version():
    file_list = None
    stable_version_url = 'https://googlechromelabs.github.io/chrome-for-testing/#stable'

    tree = soup(requests.get(stable_version_url).text, 'html.parser')

    if platform.system() == 'Darwin':
        file_list = [s for s in listdir(apple_version_path) if re.search(regex_pattern, s) is not None]
    elif platform.system() == 'Windows':
        file_list = [s for s in listdir(windows_version_path) if re.search(regex_pattern, s) is not None]

    pass
