#!/bin/bash

echo "Uninstalling Personal-project..."

python3 -m pip uninstall Personal-project -y

echo ""
echo "Removing saved data..."

rm -rf SaveData

echo ""
echo "Uninstall completed."
