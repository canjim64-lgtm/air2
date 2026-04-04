#!/bin/bash
# AirOne Professional v4.0 - Quick Installer

echo "Running AirOne Python Installer..."
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.8+ required"
    exit 1
fi

# Run Python installer
python3 install.py

echo "Done! Run: python3 launcher.py"