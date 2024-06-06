from setuptools import setup, find_packages

setup(
    name='tt_jobs',
    version='1.0',
    packages=find_packages(include=['tt_jobs', 'tt_jobs.*']),
    install_requires=['tt_interpolation', 'tt_job_manager']
)