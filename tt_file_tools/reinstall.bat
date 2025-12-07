py %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

py -m pip uninstall tt_file_tools -y
py -m pip install ./tt_file_tools

py %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
