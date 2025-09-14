python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_google_drive -y
pip install ./tt_google_drive

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
