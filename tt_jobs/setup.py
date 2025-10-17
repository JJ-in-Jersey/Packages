from setuptools import setup, find_packages

setup(
    name='tt_jobs',
    version='0.0.2',
    packages=find_packages(),
    install_requires=['tt_gpx', 'tt_job_manager', 'tt_globals', 'tt_date_time_tools', 'tt_geometry', 'tt_interpolation', 'tt_gpx']
)
