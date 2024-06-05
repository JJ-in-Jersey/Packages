from setuptools import setup, find_packages

setup(
    name='tt_globals',
    version='1.1',
    packages=find_packages(include=['tt_globals', 'tt_globals.*']),
    install_requires=['num2words']
)