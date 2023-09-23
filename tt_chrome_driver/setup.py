from setuptools import setup, find_packages

setup(
    name='tt_chrome_driver',
    version='1.3',
    packages=find_packages(include=['tt_chrome_driver', 'tt_chrome_driver.*']),
    install_requires=['selenium', 'bs4', 'requests', 'packaging', 'tt_os_abstraction']
)
