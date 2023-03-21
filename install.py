import os
import shutil
from pathlib import Path
import site

if __name__ == '__main__':

    print(f'>> package installer')

    source = os.getcwd()
    source_packages = [folder if Path(os.path.join(os.path.join(source, folder), '__init__.py')).exists() else None for folder in os.listdir(source)]
    source_packages = list(filter(lambda n: n is not None, source_packages))

    destination = Path(site.USER_SITE)
    os.makedirs(destination, exist_ok=True)

    for package in source_packages:
        if os.path.exists(os.path.join(destination, package)):
            print(f'Deleting package {package} from {destination}')
            shutil.rmtree(os.path.join(destination, package))

    for package in source_packages:
        print(f'Copying package {package} from {source} to {destination}')
        shutil.copytree(os.path.join(source, package), os.path.join(destination, package))
