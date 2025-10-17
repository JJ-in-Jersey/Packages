from setuptools import setup, find_packages

setup(
    name='tt_noaa_data',
    version='0.0.2',
    packages=find_packages(),
    install_requires=['requests', 'pandas', 'tt_globals', 'tt_file_tools', 'tt_gpx']
)
