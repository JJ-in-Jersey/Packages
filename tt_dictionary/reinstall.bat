python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

python -m pip cache purge
cd %userprofile%/PycharmProjects/Packages

python -m pip uninstall tt_dictionary -y
python -m pip install ./tt_dictionary

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause