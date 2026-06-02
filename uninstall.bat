@echo off
echo Uninstalling One_bot_to_save_em_all...

pip uninstall One_bot_to_save_em_all -y

echo.
echo Removing saved data...

rmdir /s /q SaveData

echo.
echo Uninstall completed.

pause