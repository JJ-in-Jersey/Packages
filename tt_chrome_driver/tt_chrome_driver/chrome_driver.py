from pathlib import Path
from os import listdir
import re
import platform
import requests
from bs4 import BeautifulSoup as Soup
from packaging.version import Version
from urllib.request import urlretrieve
from time import sleep

# import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from tt_os_abstraction.os_abstraction import env


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


class ChromeDriver:

    def get_driver(self, download_dir=None, headless=False):
        if self.lookup['driver_file'].exists():
            prefs = {'download.prompt_for_download': False, 'safebrowsing.enabled': True,
                     'profile.default_content_setting_values.notifications': 2}
            if download_dir is not None: prefs['download.default_directory'] = str(download_dir)
            my_options = Options()
            my_options.add_experimental_option('prefs', prefs)
            my_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # my_options.add_argument("--incognito")
            if headless: my_options.add_argument('--headless=new')
            driver = webdriver.Chrome(service=Service(str(self.lookup['driver_file'])), options=my_options)
            driver.implicitly_wait(10)  # seconds
            if not headless: driver.minimize_window()
        else:
            raise Exception('chrome driver not found: ' + str(self.lookup['driver_file']))
        return driver

    def page_source(self, url, headless=False):
        driver = self.get_driver(None, headless)
        driver.get(url)
        sleep(5)  # seconds
        source = driver.page_source
        driver.quit()
        return source

    def check_driver(self):
        if not self.lookup['chrome_exe_file'].exists():
            raise Exception('chrome is not installed')

        print(f'latest stable version: {self.latest_stable_version}')
        print(f'installed driver version: {self.installed_driver_version}')
        print(f'installed chrome version: {self.installed_chrome_version}')

        # if not self.installed_driver_version == self.latest_stable_version:
        #     print(f'downloading latest stable chromedriver version: {download_latest_stable_driver_version()}')
        #     print(f'driver folder: {self.lookup["driver_folder"]}')
        #
        # if not self.installed_chrome_version >= self.latest_stable_version:
        #     print(f'downloading latest stable chrome version: {download_latest_stable_chrome_version()}')

    def __init__(self):
        stable_version_url = 'https://googlechromelabs.github.io/chrome-for-testing/#stable'
        tree = Soup(requests.get(stable_version_url).text, 'html.parser')
        self.latest_stable_version = Version(tree.find(id='stable').find('p').find('code').text)

        apple_lookup = {'chrome_exe_file': Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                        'chrome_version_folder': Path('/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions'),
                        'version_regex': 'chromedriver-[0-9,.]',
                        'version_list_lambda': (lambda string: Version(string.split('-')[1])),
                        'driver_folder': Path('/usr/local/bin/chromedriver/'),
                        'driver_file': None}
        windows_lookup = {'chrome_exe_file': Path('C:/Program Files/Google/Chrome/Application/Chrome.exe'),
                          'chrome_version_folder': Path(env('user_profile') + '/AppData/local/Google/chromedriver/'),
                          'version_regex': 'chromedriver-[0-9,.]+.exe',
                          'version_list_lambda': (lambda string: Version(string.split('-')[1].rsplit('.', 1)[0])),
                          'driver_folder': Path('C:/Program Files/Google/Chrome/Application'),
                          'driver_file': None}

        if platform.system() == "Darwin": self.lookup = apple_lookup
        elif platform.system() == 'Windows': self.lookup = windows_lookup

        driver_version_list = [self.lookup['version_list_lambda'](s) for s in listdir(self.lookup['driver_folder']) if re.search(self.lookup['version_regex'], s) is not None]
        driver_version_list.sort()
        self.installed_driver_version = driver_version_list[-1]

        regex_pattern = '^[0-9\.]*$'
        chrome_version_list = [Version(s) for s in listdir(self.lookup['chrome_version_folder']) if re.search(regex_pattern, s) is not None]
        chrome_version_list.sort()
        self.installed_chrome_version = chrome_version_list[-1]

        apple_lookup['driver_file'] = apple_lookup['driver_folder'].joinpath('chromedriver-' + str(self.installed_driver_version))
        windows_lookup['driver_file'] = windows_lookup['driver_folder'].joinpath('chromedriver-' + str(self.installed_driver_version) + '.exe')
