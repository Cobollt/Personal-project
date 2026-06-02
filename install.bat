@echo off
echo Installing One_bot_to_save_em_all...

python -m pip install --upgrade pip
python -m pip install . --force-reinstall

echo.
echo Installation completed.
echo To start the bot, use:
echo assistant-bot
echo.

pause