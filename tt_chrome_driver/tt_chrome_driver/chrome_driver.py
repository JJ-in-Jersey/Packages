from pathlib import Path
import platform
import chromedriver_autoinstaller

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from tt_os_abstraction.os_abstraction import temp

logger = logging.getLogger('selenium')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(Path(temp() + '/logfile.tmp'))
logger.addHandler(handler)


def get_driver(download_dir=None):
    print(f'chrome version: {chromedriver_autoinstaller.get_chrome_version()}')
    print(f'isChromeInstalled: {is_chrome_installed()}')
    chromedriver_autoinstaller.install()
    my_options = Options()
    if download_dir is not None:
        my_options.add_experimental_option("prefs", {'download.default_directory': str(download_dir)})
    driver = webdriver.Chrome(options=my_options)
    driver.implicitly_wait(10)  # seconds
    driver.minimize_window()
    return driver


def is_chrome_installed():
    apple_path = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    windows_path = Path('C:/Program Files/Google/Chrome/Application/Chrome.exe')

    if platform.system() == 'Darwin':
        return apple_path.exists()
    elif platform.system() == 'Windows':
        return windows_path.exists()
    pass