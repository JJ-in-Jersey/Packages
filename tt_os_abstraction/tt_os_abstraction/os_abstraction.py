from os import environ
from pathlib import Path
import platform

if platform.system() == 'Darwin':
    platform_lookup = {
                    'user_profile': Path(environ['HOME']),
                    'temp': Path(environ['TMPDIR']),
                    'system': 'mac-arm64',
                    'os': 'mac',
                    'driver_regex': 'chromedriver-[0-9,.]',
                    'driver_folder': Path('/usr/local/bin/chromedriver/'),
                    'browser_exe': Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                    'user_data': Path(environ['HOME']).joinpath('Library/Application Support/Google/Chrome/Default')
                    }
elif platform.system() == 'Windows':
    platform_lookup = {
                    'user_profile': Path(environ['USERPROFILE']),
                    'temp': Path(environ['TEMP']),
                    'system': 'win64',
                    'os': 'win',
                    'driver_regex': 'chromedriver-[0-9,.]+.exe',
                    'driver_folder': Path(environ['USERPROFILE'] + '/AppData/local/Google/chromedriver/'),
                    'browser_exe': Path('C:/Program Files/Google/Chrome/Application/Chrome.exe'),
                    'user_data': Path(environ['USERPROFILE']).joinpath('AppData/Local/Google/Chrome/User Data')
                    }


def env(var_name):
    return platform_lookup[var_name]

