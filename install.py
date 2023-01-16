import os
from pathlib import Path
import site
from os import makedirs, getcwd

if __name__ == '__main__':

    print(f'>> package installer')

    us = Path(site.USER_SITE)
    if not us.exists(): makedirs(us)

    cwd = Path(getcwd())
    for i in os.listdir(cwd):
        if os.path.isdir(i):
            print(type(i))





