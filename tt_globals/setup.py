from setuptools import setup, find_packages

setup(
    name='tt_globals',
    version='1.0',
    packages=find_packages(include=['tt_globals', 'tt_globals.*']),
)