#!/bin/bash

# SriDAW Setup Script
# This script installs all dependencies and sets up the environment

echo "Setting up SriDAW environment..."

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3.13-venv python3-pip libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good build-essential

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment and install Python dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Setup complete!"
echo "To run SriDAW, use: ./run_app.sh"
echo "To build Android APK, use: ./build.sh"