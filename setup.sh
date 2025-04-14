#!/bin/bash

# Divoom Linux Monitor Tool Setup Script

echo "=== Divoom Linux Monitor Tool Setup ==="
echo "This script will install required dependencies"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./setup.sh)"
  exit 1
fi

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y python3 python3-pip lm-sensors hddtemp smartmontools nvme-cli

# Configure sensors
echo "Configuring hardware sensors..."
sensors-detect --auto
service kmod start

# Install Python dependencies
echo "Installing Python packages..."
pip3 install requests

# Make scripts executable
chmod +x run.sh
chmod +x src/divoom_monitor.py

echo "Setup complete! To run the application:"
echo "  ./run.sh        : Regular mode"
echo "  ./run.sh --debug: Debug mode"
echo "  ./run.sh --restart: Auto-restart mode"
echo ""
echo "See README.md for more information" 