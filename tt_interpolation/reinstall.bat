python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

python -m pip cache purge
cd %userprofile%/PycharmProjects/Packages

python -m pip uninstall tt_interpolation -y
python -m pip install ./tt_interpolation

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause