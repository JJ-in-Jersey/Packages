
python %userprofile%/PycharmProjects/Packages/bin/cleanup.py

pip cache purge
pip freeze > %TMP%\pip_freeze
pip uninstall -y -r %TMP%\pip_freeze

pause