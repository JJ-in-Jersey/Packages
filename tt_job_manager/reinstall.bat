py %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
cd %userprofile%/PycharmProjects/Packages

py -m pip uninstall tt_job_manager -y
py -m pip install ./tt_job_manager

py %userprofile%/PycharmProjects/Packages/bin/cleanup.py
pause
