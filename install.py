import os
import shutil
from pathlib import Path
import site
from shutil import copytree

if __name__ == '__main__':

    print(f'>> package installer')

    source = os.getcwd()
    source_packages = [dir if Path(os.path.join(os.path.join(source,dir), '__init__.py')).exists() else None for dir in os.listdir(source)]
    while None in source_packages: source_packages.remove(None)

    destination = Path(site.USER_SITE)
    if destination.exists():
        destination_packages = [dir for dir in os.listdir(destination)]

        for package in destination_packages:
            print(f'Delete package {package} from {destination}')
            shutil.rmtree(os.path.join(destination, package))

    for package in source_packages:
        print(f'Copying package {package} from {source} to {destination}')
        shutil.copytree(os.path.join(source,package), os.path.join(destination,package))









