from setuptools import setup, find_packages

setup(
    name='tt_semaphore',
    version='1.0',
    packages=find_packages(include=['tt_semaphore', 'tt_semaphore.*']),
    install_requires=['tt_os_abstraction']
)
