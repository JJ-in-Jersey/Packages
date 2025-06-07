python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_interpolation -y
pip install ./tt_interpolation

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause