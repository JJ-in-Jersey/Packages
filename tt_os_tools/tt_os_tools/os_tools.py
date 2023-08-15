from os import environ
import platform


class UserProfile:

    USER_PROFILE = None

    def __init__(self):
        if platform.system() == 'Darwin':
            UserProfile.USER_PROFILE = environ['HOME']
        elif platform.system() == 'Windows':
            UserProfile.USER_PROFILE = environ['USERPROFILE']


class Temp:

    TEMP = None

    def __init__(self):
        if platform.system() == 'Darwin':
            Temp.TEMP = environ['TMPDIR']
        elif platform.system() == 'Windows':
            Temp.TEMP = environ['TEMP']