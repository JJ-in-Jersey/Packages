from pathlib import Path
from os import listdir
import re
import platform
import requests
from bs4 import BeautifulSoup as Soup
from packaging.version import Version
from urllib.request import urlretrieve

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from tt_os_abstraction.os_abstraction import env

logger = logging.getLogger('selenium')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(Path(env('temp') + '/logfile.tmp'))
logger.addHandler(handler)


def get_driver(download_dir=None):

    driver_path = get_installed_driver_path()
    if driver_path.exists():
        my_options = Options()
        my_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        if download_dir is not None:
            (my_options.add_experimental_option("prefs", {'download.default_directory': str(download_dir)}))
        driver = webdriver.Chrome(service=Service(str(driver_path)), options=my_options)
        driver.implicitly_wait(10)  # seconds
        driver.minimize_window()
    else:
        raise Exception('chrome driver not found: ' + str(driver_path))

    return driver


def is_chrome_installed():
    path = get_installed_chrome_path()
    if path.exists():
        return True
    else:
        return False


def get_installed_chrome_version():
    apple_version_path = Path('/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions')
    windows_version_path = Path('C:/Program Files/Google/Chrome/Application')

    regex_pattern = '^[0-9\.]*$'

    version_list = None
    if platform.system() == 'Darwin':
        version_list = [Version(s) for s in listdir(apple_version_path) if re.search(regex_pattern, s) is not None]
    elif platform.system() == 'Windows':
        version_list = [Version(s) for s in listdir(windows_version_path) if re.search(regex_pattern, s) is not None]

    version_list.sort()
    return version_list[-1]


def get_latest_stable_chrome_version():
    stable_version_url = 'https://googlechromelabs.github.io/chrome-for-testing/#stable'
    tree = Soup(requests.get(stable_version_url).text, 'html.parser')
    return Version(tree.find(id='stable').find('p').find('code').text)


def download_latest_stable_chrome_version():
    stable_version_url = 'https://googlechromelabs.github.io/chrome-for-testing/#stable'
    url = None

    tree = Soup(requests.get(stable_version_url).text, 'html.parser')
    version = tree.find(id='stable').find('p').find('code').text

    if platform.system() == 'Darwin':
        url = tree.find(id='stable').find(text='chrome').find_next(text='mac-arm64').find_next('code').text
    elif platform.system() == 'Windows':
        url = tree.find(id='stable').find(text='chrome').find_next(text='win64').find_next('code').text

    filename = Path(env('user_profile') + '/Downloads/' + str(version) + '-' + url.rpartition('/')[2])
    return urlretrieve(url, filename)[0]


def download_latest_stable_driver_version():
    stable_version_url = 'https://googlechromelabs.github.io/chrome-for-testing/#stable'
    url = None

    tree = Soup(requests.get(stable_version_url).text, 'html.parser')
    version = tree.find(id='stable').find('p').find('code').text
    if platform.system() == 'Darwin':
        url = tree.find(id='stable').find(text='chromedriver').find_next(text='mac-arm64').find_next('code').text
    elif platform.system() == 'Windows':
        url = tree.find(id='stable').find(text='chromedriver').find_next(text='win64').find_next('code').text

    filename = Path(env('user_profile') + '/Downloads/' + str(version) + '-' + url.rpartition('/')[2])
    return urlretrieve(url, filename)[0]


apple_driver_folder = Path('/usr/local/bin/chromedriver/')
windows_driver_folder = Path(env('user_profile') + '/AppData/local/Google/chromedriver/')


def get_installed_driver_version():
    version_list = None
    if platform.system() == 'Darwin':
        regex_pattern = 'chromedriver-[0-9,.]'
        version_list = [Version(s.split('-')[1]) for s in listdir(apple_driver_folder) if re.search(regex_pattern, s) is not None]
    elif platform.system() == 'Windows':
        regex_pattern = 'chromedriver-[0-9,.]+.exe'
        version_list = [Version(s.split('-')[1].rsplit('.',1)[0]) for s in listdir(windows_driver_folder) if re.search(regex_pattern, s) is not None]

    version_list.sort()
    return version_list[-1]


def get_installed_driver_path():
    if platform.system() == 'Darwin':
        return apple_driver_folder.joinpath('chromedriver-' + str(get_installed_driver_version()))
    elif platform.system() == 'Windows':
        return windows_driver_folder.joinpath('chromedriver-' + str(get_installed_driver_version()) + '.exe')


def get_installed_chrome_path():
    apple_exe_path = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    windows_exe_path = Path('C:/Program Files/Google/Chrome/Application/Chrome.exe')

    if platform.system() == 'Darwin':
        return apple_exe_path
    elif platform.system() == 'Windows':
        return windows_exe_path
