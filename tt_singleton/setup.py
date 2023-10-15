from setuptools import setup, find_packages

setup(
    name='tt_singleton',
    version='1.0',
    packages=find_packages(include=['tt_singleton', 'tt_singleton.*']),
)