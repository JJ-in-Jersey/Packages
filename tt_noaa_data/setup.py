from setuptools import setup, find_packages

setup(
    name='tt_noaa_data',
    packages=find_packages(include=['tt_noaa_data', 'tt_noaa_data.*']),
    install_requires=['requests', 'pandas', 'tt_globals', 'tt_file_tools', 'tt_gpx']
)
