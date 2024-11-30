from setuptools import setup, find_packages

setup(
    name='tt_geometry',
    packages=find_packages(include=['tt_geometry', 'tt_geometry.*']),
    install_requires=['pandas']
)
