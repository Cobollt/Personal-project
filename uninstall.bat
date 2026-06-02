@echo off
echo Uninstalling Personal-project...

python -m pip uninstall Personal-project -y

echo.
echo Removing saved data...

rmdir /s /q SaveData

echo.
echo Uninstall completed.
pause