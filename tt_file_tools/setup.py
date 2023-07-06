from setuptools import setup, find_packages

setup(
    name='tt_file_tools',
    version='1.0',
    packages=find_packages(include=['tt_file_tools', 'tt_file_tools.*']),
    install_requires=['pandas', 'numpy', 'tt_memory_helper']
)
