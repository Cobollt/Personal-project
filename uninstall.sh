#!/bin/bash

echo "Uninstalling One_bot_to_save_em_all..."

python3 -m pip uninstall One_bot_to_save_em_all -y

echo ""
echo "Removing saved data..."

rm -rf SaveData

echo ""
echo "Uninstall completed."
