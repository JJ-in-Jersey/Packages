from setuptools import setup, find_packages

setup(
    name='tt_semaphore',
    packages=find_packages(include=['tt_semaphore', 'tt_semaphore.*']),
    install_requires=['tt_os_abstraction']
)
