from setuptools import setup, find_packages

setup(
    name='tt_job_manager',
    packages=find_packages(include=['tt_job_manager', 'tt_job_manager.*']),
    install_requires=['tt_singleton', 'tt_semaphore']
)