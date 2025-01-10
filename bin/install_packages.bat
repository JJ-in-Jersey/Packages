cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_date_time_tools -y
pip uninstall tt_file_tools -y
pip uninstall tt_geometry -y
pip uninstall tt_globals -y
pip uninstall tt_gpx -y
pip uninstall tt_interpolation -y
pip uninstall tt_job_manager -y
pip uninstall tt_jobs -y
pip uninstall tt_os_abstraction -y
pip uninstall tt_navigation -y
pip uninstall tt_noaa_data -y
pip uninstall tt_semaphore -y
pip uninstall tt_singleton -y
pip uninstall tt_chrome_driver -y

pip install ./tt_singleton
pip install ./tt_navigation
pip install ./tt_date_time_tools
pip install ./tt_file_tools
pip install ./tt_geometry
pip install ./tt_globals
pip install ./tt_gpx
pip install ./tt_interpolation
pip install ./tt_job_manager
pip install ./tt_os_abstraction
pip install ./tt_noaa_data
pip install ./tt_semaphore
REM pip install ./tt_chrome_driver
REM pip install ./tt_jobs

pause
