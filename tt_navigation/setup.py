from setuptools import setup, find_packages

setup(
    name='tt_navigation',
    version='1.2',
    packages=find_packages(include=['tt_navigation', 'tt_navigation.*']),
    install_requires=['haversine', 'numpy']
)
