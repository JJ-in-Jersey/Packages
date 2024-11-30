from setuptools import setup, find_packages

setup(
    name='tt_navigation',
    packages=find_packages(include=['tt_navigation', 'tt_navigation.*']),
    install_requires=['haversine', 'numpy']
)
