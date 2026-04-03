#!/bin/bash
# AirOne Professional v4.0 - Quick Installer

echo "Installing AirOne..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.8+ required"
    exit 1
fi

# Install deps
pip3 install numpy psutil requests flask pyjwt cryptography pillow

echo "Done! Run: python3 main.py"