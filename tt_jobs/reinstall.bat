python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

pip uninstall tt_jobs -y
pip install ./tt_jobs

python %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
