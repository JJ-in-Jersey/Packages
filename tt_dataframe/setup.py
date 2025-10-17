from setuptools import setup, find_packages

setup(
    name='tt_dataframe',
    packages=find_packages(include=['tt_dataframe', 'tt_dataframe.*']),
    install_requires=['tt_exceptions', 'polars', 'pyarrow']
)
