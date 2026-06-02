@echo off
echo Installing Personal-project...

python -m pip install --upgrade pip
python -m pip install . --force-reinstall

echo.
echo Installation completed.
echo Run the bot with:
echo assistant
pause