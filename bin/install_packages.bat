cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_memory_helper -y
pip uninstall tt_navigation -y
pip uninstall tt_chrome_driver -y
pip uninstall tt_date_time_tools -y
pip uninstall tt_file_tools -y
pip uninstall tt_geometry -y
pip uninstall tt_gpx -y
pip uninstall tt_interpolation -y
pip uninstall tt_semaphore -y


pip install ./tt_memory_helper
pip install ./tt_navigation
pip install ./tt_chrome_driver
pip install ./tt_date_time_tools
pip install ./tt_file_tools
pip install ./tt_geometry
pip install ./tt_gpx
pip install ./tt_interpolation
pip install ./tt_semaphore
