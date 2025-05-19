for /f "tokens=1" %%a in ('cd') do (set pwd=%%a)

cd ..
pip uninstall tt_inflection -y
pip install ./tt_inflection

cd %pwd%
pause