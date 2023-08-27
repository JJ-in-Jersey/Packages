from os import environ
import platform

platform_lookup = { 'darwin': {'user_profile': 'HOME', 'temp': 'TMPDIR'}, 'windows': {'user_profile': 'USERPROFILE', 'temp': 'TEMP'}}


def env(var_name):
    return platform_lookup[platform.system()][var_name]


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
