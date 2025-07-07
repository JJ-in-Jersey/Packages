
python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
pip install setuptools

cd %userprofile%/PycharmProjects/Packages

pip install ./tt_interpolation
pip install ./tt_os_abstraction
pip install ./tt_navigation
pip install ./tt_singleton
pip install ./tt_semaphore
pip install ./tt_exceptions
pip install ./tt_dataframe
pip install ./tt_dictionary
pip install ./tt_date_time_tools
pip install ./tt_file_tools
pip install ./tt_geometry
pip install ./tt_globals
pip install ./tt_gpx
pip install ./tt_job_manager
pip install ./tt_noaa_data
pip install ./tt_jobs

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pip list

pause
