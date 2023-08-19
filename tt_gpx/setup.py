from setuptools import setup, find_packages

setup(
    name='tt_gpx',
    version='1.0',
    packages=find_packages(include=['tt_gpx', 'tt_gpx.*']),
    install_requires=['bs4', 'lxml', 'tt_navigation']
)
