from setuptools import setup, find_packages

setup(
    name='tt_memory_helper',
    version='1.0',
    packages=find_packages(include=['tt_memory_helper', 'tt_memory_helper.*']),
    install_requires=['pandas', 'numpy']
)
