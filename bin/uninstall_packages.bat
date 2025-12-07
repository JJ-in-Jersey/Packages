
py %userprofile%/PycharmProjects/Packages/bin/cleanup.py

py -m pip cache purge
py -m pip freeze > %TMP%\pip_freeze
py -m pip uninstall -y -r %TMP%\pip_freeze
py -m pip list

py %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pause