from os import environ
from pathlib import Path
import platform


if platform.system() == 'Darwin':
    platform_lookup = {
                    'user_profile': environ['HOME'],
                    'temp': environ['TMPDIR'],
                    'system': 'mac-arm64',
                    'driver_regex': 'chromedriver-[0-9,.]',
                    'driver_folder': Path('/usr/local/bin/chromedriver/'),
                    'browser_exe': Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
                    }
elif platform.system() == 'Windows':
    platform_lookup = {
                    'user_profile': environ['USERPROFILE'],
                    'temp': environ['TEMP'],
                    'system': 'win64',
                    'driver_regex': 'chromedriver-[0-9,.]+.exe',
                    'driver_folder': Path(environ['USERPROFILE'] + '/AppData/local/Google/chromedriver/'),
                    'browser_exe': Path('C:/Program Files/Google/Chrome/Application/Chrome.exe')
                    }


def env(var_name):
    return platform_lookup[var_name]


# def user_profile():
#     if platform.system() == 'Darwin':
#         return environ['HOME']
#     elif platform.system() == 'Windows':
#         return environ['USERPROFILE']
#
#
# def temp():
#     if platform.system() == 'Darwin':
#         return environ['TMPDIR']
#     elif platform.system() == 'Windows':
#         return environ['TEMP']
