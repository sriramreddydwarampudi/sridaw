#!/bin/bash

# SriDAW - Run Script
# This script activates the virtual environment and runs the SriDAW application

echo "Starting SriDAW..."

# Activate virtual environment
source venv/bin/activate

# Run the application
echo "Running SriDAW with Python $(python3 --version)"
python3 main.py

echo "SriDAW ended."