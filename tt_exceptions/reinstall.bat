python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_exceptions -y
pip install ./tt_exceptions

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
