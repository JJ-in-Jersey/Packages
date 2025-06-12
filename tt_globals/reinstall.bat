python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_globals -y
pip install ./tt_globals

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
