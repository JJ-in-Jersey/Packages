for /f "tokens=1" %%a in ('cd') do (set pwd=%%a)

cd ..
pip uninstall tt_globals -y
pip install ./tt_globals

cd %pwd%
pause
