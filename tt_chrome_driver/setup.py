from setuptools import setup, find_packages

setup(
    name='tt_chrome_driver',
    packages=find_packages(include=['tt_chrome_driver', 'tt_chrome_driver.*']),
    install_requires=['zipfile', 'selenium', 'bs4', 'requests', 'packaging', 'tt_os_abstraction']
)
