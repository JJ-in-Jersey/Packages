from setuptools import setup, find_packages

setup(
    name='tt_interpolation',
    version='1.0',
    packages=find_packages(include=['tt_interpolation', 'tt_interpolation.*']),
    install_requires=['scipy', 'numpy', 'sympy', 'matplotlib']
)