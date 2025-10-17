from setuptools import setup, find_packages

setup(
    name='tt_gpx',
    version='0.0.2',
    packages=find_packages(),
    install_requires=['beautifulsoup4', 'lxml', 'num2words', 'tt_globals', 'tt_navigation', 'tt_file_tools']
)
