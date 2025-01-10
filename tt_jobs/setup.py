from setuptools import setup, find_packages

setup(
    name='tt_jobs',
    packages=find_packages(include=['tt_jobs', 'tt_jobs.*']),
    install_requires=['sympy', 'tt_interpolation', 'tt_job_manager']
)
