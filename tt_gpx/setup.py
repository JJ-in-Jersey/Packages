from setuptools import setup, find_packages

setup(
    name='tt_gpx',
    packages=find_packages(include=['tt_gpx', 'tt_gpx.*']),
    install_requires=['bs4', 'lxml', 'tt_navigation', 'tt_jobs', 'tt_file_tools']
)
