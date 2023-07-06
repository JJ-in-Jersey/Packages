from setuptools import setup, find_packages

setup(
    name='tt_chrome_driver',
    version='1.0',
    # packages=find_packages(include=['chrome_driver'])
    # py_modules=['chrome_driver']
    packages=find_packages(include=['tt_chrome_driver', 'tt_chrome_driver.*']),
    install_requires = [ 'os', 'selenium', 'logging', 'webdriver_manager.chrome']
)
