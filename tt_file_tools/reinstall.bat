python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_file_tools -y
pip install ./tt_file_tools

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
