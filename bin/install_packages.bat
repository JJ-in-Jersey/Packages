
py %userprofile%/PycharmProjects/Packages/bin/cleanup.py

py -m pip cache purge
py -m pip install setuptools
py -m pip install pandas-stubs
py -m pip install scipy-stubs
py -m pip install google-api-python-client
py -m pip install google-auth-httplib2
py -m pip install google-auth-oauthlib

cd %userprofile%/PycharmProjects/Packages

py -m pip install ./tt_interpolation
py -m pip install ./tt_os_abstraction
py -m pip install ./tt_navigation
py -m pip install ./tt_singleton
py -m pip install ./tt_semaphore
py -m pip install ./tt_exceptions
py -m pip install ./tt_dataframe
py -m pip install ./tt_dictionary
py -m pip install ./tt_date_time_tools
py -m pip install ./tt_file_tools
py -m pip install ./tt_geometry
py -m pip install ./tt_globals
py -m pip install ./tt_google_drive
py -m pip install ./tt_gpx
py -m pip install ./tt_job_manager
py -m pip install ./tt_noaa_data
py -m pip install ./tt_jobs

py %userprofile%/PycharmProjects/Packages/bin/cleanup.py
py -m pip list

pause
