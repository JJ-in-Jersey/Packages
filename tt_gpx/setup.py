from setuptools import setup, find_packages

setup(
    name='tt_gpx',
    packages=find_packages(include=['tt_gpx', 'tt_gpx.*']),
    install_requires=['Beautifulsoup4', 'lxml', 'num2words', 'tt_globals', 'tt_navigation', 'tt_file_tools']
)
