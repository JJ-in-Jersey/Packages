python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_noaa_data -y
pip install ./tt_noaa_data

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause