from os import environ
import platform


def user_profile():
    if platform.system() == 'Darwin':
        return environ['HOME']
    elif platform.system() == 'Windows':
        return environ['USERPROFILE']


def temp():
    if platform.system() == 'Darwin':
        return environ['TMPDIR']
    elif platform.system() == 'Windows':
        return environ['TEMP']
