python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_dictionary -y
pip install ./tt_dictionary

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause