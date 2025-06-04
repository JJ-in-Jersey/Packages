python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_dataframe -y
pip install ./tt_dataframe

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause