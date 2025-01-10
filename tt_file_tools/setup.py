from setuptools import setup, find_packages

setup(
    name='tt_file_tools',
    packages=find_packages(include=['tt_file_tools', 'tt_file_tools.*']),
    install_requires=['numpy', 'pandas', 'bs4']
)
