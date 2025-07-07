#!/bin/sh

python %HOME/PycharmProjects/Packages/bin/cleanup.py

pip3 cache purge
pip3 install setuptools

cd $HOME/PycharmProjects/Packages

pip3 install ./tt_interpolation
pip3 install ./tt_os_abstraction
pip3 install ./tt_navigation
pip3 install ./tt_singleton
pip3 install ./tt_semaphore
pip3 install ./tt_exceptions
pip3 install ./tt_dataframe
pip3 install ./tt_dictionary
pip3 install ./tt_date_time_tools
pip3 install ./tt_file_tools
pip3 install ./tt_geometry
pip3 install ./tt_globals
pip3 install ./tt_gpx
pip3 install ./tt_job_manager
pip3 install ./tt_noaa_data
pip3 install ./tt_jobs

python %HOME/PycharmProjects/Packages/bin/cleanup.py