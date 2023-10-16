#!/bin/sh

cd $HOME/PycharmProjects/Packages

pip3 uninstall tt_singleton -y
pip3 uninstall tt_navigation -y
pip3 uninstall tt_date_time_tools -y
pip3 uninstall tt_file_tools -y
pip3 uninstall tt_geometry -y
pip3 uninstall tt_gpx -y
pip3 uninstall tt_interpolation -y
pip3 uninstall tt_os_abstraction -y
pip3 uninstall tt_semaphore -y
pip3 uninstall tt_chrome_driver -y
pip3 uninstall tt_job_manager -y

pip3 install ./tt_singleton
pip3 install ./tt_navigation
pip3 install ./tt_date_time_tools
pip3 install ./tt_file_tools
pip3 install ./tt_geometry
pip3 install ./tt_gpx
pip3 install ./tt_interpolation
pip3 install ./tt_os_abstraction
pip3 install ./tt_semaphore
pip3 install ./tt_chrome_driver
pip3 install ./tt_job_manager
