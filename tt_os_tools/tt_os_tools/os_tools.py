from pathlib import Path
from os import environ
import platform

if platform.system() == 'Darwin':
    user_profile = environ['HOME']
    temp = environ['TMPDIR']
elif platform.system() == 'Windows':
    user_profile = environ['USERPROFILE']
    temp = environ['TEMP']

