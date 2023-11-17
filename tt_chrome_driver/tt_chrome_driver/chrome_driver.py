from pathlib import Path
from os import listdir, replace, chmod
import re
import platform
import requests
from bs4 import BeautifulSoup as Soup
from packaging.version import Version
from urllib.request import urlretrieve
from time import sleep
import zipfile

# import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from tt_os_abstraction.os_abstraction import env


class ChromeDriver:

    def get_driver(self, download_dir=None):
        if self.installed_driver_file.exists():
            prefs = {'download.prompt_for_download': False, 'safebrowsing.enabled': True,
                     'profile.default_content_setting_values.notifications': 2}
            if download_dir is not None: prefs['download.default_directory'] = str(download_dir)
            my_options = Options()
            my_options.add_experimental_option('prefs', prefs)
            my_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # my_options.add_argument("--incognito")
            # my_options.add_argument(r'--user-data-dir=' + str(env('user_data')))
            driver = webdriver.Chrome(service=Service(str(self.installed_driver_file)), options=my_options)
            driver.implicitly_wait(10)  # seconds
            # driver.minimize_window()
        else:
            raise Exception('chrome driver not found: ' + str(self.installed_driver_file))
        return driver

    def page_source(self, url):
        driver = self.get_driver()
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

    def install_stable_driver(self):
        downloads = Path(env('user_profile')).joinpath('Downloads')
        file = downloads.joinpath(str(self.latest_stable_version) + '-' + self.lookup['download_url'].rpartition('/')[2])
        zip_file = zipfile.ZipFile(urlretrieve(self.lookup['download_url'], file)[0], 'r')
        with zip_file as zf: zf.extractall(downloads)
        source = downloads.joinpath(list(filter(lambda s: 'LICENSE' not in s, zip_file.namelist()))[0])
        self.installed_driver_file = self.lookup['driver_folder'].joinpath('chromedriver' + self.lookup['driver_suffix'])
        replace(source, self.installed_driver_file)
        chmod(self.installed_driver_file, 777)

    def __init__(self):
        stable_version_url = 'https://googlechromelabs.github.io/chrome-for-testing/#stable'
        tree = Soup(requests.get(stable_version_url).text, 'html.parser')
        self.latest_stable_version = Version(tree.find(id='stable').find('p').find('code').text)

        driver_base_name = 'chromedriver'
        windows_lookup = {'chrome_exe_file': Path('C:/Program Files/Google/Chrome/Application/Chrome.exe'),
                          'chrome_version_folder': Path('C:/Program Files/Google/Chrome/Application'),
                          'version_extract': lambda name: Version(name.split('-')[1].rsplit('.', 1)[0]),
                          'driver_folder': env('user_profile').joinpath('AppData/local/Google/chromedriver/'),
                          'driver_suffix': '-' + str(self.latest_stable_version) + '.exe',
                          'download_url': tree.find(id='stable').find(text='chromedriver').find_next(text='win64').find_next('code').text}

        apple_lookup = {'chrome_exe_file': Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                        'chrome_version_folder': Path('/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions'),
                        'version_extract': lambda name: Version(name.split('-')[1]),
                        'driver_folder': Path('/usr/local/bin/chromedriver/'),
                        'driver_suffix': '-' + str(self.latest_stable_version),
                        'download_url': tree.find(id='stable').find(text='chromedriver').find_next(text='mac-arm64').find_next('code').text}

        if platform.system() == "Darwin": self.lookup = apple_lookup
        elif platform.system() == 'Windows': self.lookup = windows_lookup

        driver_version_list = [self.lookup['version_extract'](file) for file in listdir(self.lookup['driver_folder'])]
        driver_version_list.sort()
        driver_version_list.reverse()

        if len(driver_version_list):
            self.installed_driver_file = self.lookup['driver_folder'].joinpath(driver_base_name + self.lookup['driver_suffix'])
            self.installed_driver_version = driver_version_list[0]
        else:
            self.installed_driver_file = None
            self.installed_driver_version = None

        regex_pattern = '^[0-9\.]*$'
        chrome_version_list = [Version(s) for s in listdir(self.lookup['chrome_version_folder']) if re.search(regex_pattern, s) is not None]
        chrome_version_list.sort()
        self.installed_chrome_version = chrome_version_list[-1]
