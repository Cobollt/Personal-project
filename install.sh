#!/bin/bash

echo "Installing One_bot_to_save_em_all..."

python3 -m pip install --upgrade pip
python3 -m pip install . --force-reinstall

echo ""
echo "Installation completed."
echo "Run the bot with:"
echo "assistant-bot"