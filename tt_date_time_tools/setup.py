from setuptools import setup, find_packages

setup(
    name='tt_date_time_tools',
    packages=find_packages(include=['tt_date_time_tools', 'tt_date_time_tools.*']),
    install_requires=['dateparser']
)
