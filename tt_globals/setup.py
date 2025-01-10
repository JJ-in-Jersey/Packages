from setuptools import setup, find_packages

setup(
    name='tt_globals',
    packages=find_packages(include=['tt_globals', 'tt_globals.*']),
    install_requires=['tt_os_abstraction']
)
