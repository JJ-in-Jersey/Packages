python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_geometry -y
pip install ./tt_geometry

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
