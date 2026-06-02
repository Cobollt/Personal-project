#!/bin/bash

echo "Installing Personal-project..."

python3 -m pip install --upgrade pip
python3 -m pip install . --force-reinstall

echo ""
echo "Installation completed."
echo "Run the bot with:"
echo "assistant-bot"