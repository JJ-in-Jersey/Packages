from setuptools import setup, find_packages

setup(
    name='tt_job_manager',
    version='1.0',
    packages=find_packages(include=['tt_noaa_data', 'tt_noaa_data.*']),
    install_requires=[]
)
