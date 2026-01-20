python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

python -m pip cache purge
cd %userprofile%/PycharmProjects/Packages

python -m pip uninstall tt_noaa_data -y
python -m pip install ./tt_noaa_data

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause