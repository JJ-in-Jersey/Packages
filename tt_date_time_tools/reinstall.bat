python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_date_time_tools -y
pip install ./tt_date_time_tools

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause