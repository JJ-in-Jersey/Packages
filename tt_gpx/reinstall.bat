python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_gpx -y
pip install ./tt_gpx

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause