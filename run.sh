#!/bin/bash

# Divoom Linux Monitor Tool run script

# Check if running as root (required for hardware monitoring)
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo) for full hardware monitoring capabilities"
  echo "Running without root may limit available hardware information"
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Exiting. Please run with 'sudo ./run.sh'"
    exit 1
  fi
fi

# Navigate to the project directory
cd "$(dirname "$0")/src"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  echo "Python 3 not found. Please install Python 3."
  echo "sudo apt-get install python3 python3-pip"
  exit 1
fi

# Check if requests module is installed
if ! python3 -c "import requests" &> /dev/null; then
  echo "Python requests module not found. Installing..."
  pip3 install requests
  if [ $? -ne 0 ]; then
    echo "Failed to install requests module. Try installing manually:"
    echo "sudo pip3 install requests"
    exit 1
  fi
fi

# Check for hardware monitoring tools
echo "Checking for hardware monitoring tools..."
if ! command -v sensors &> /dev/null; then
  echo "lm-sensors not found. Some temperature readings may be unavailable."
  echo "Install with: sudo apt-get install lm-sensors"
fi

# Check for storage monitoring tools
STORAGE_TOOLS_FOUND=false

# Check HDD temperature tool
if command -v hddtemp &> /dev/null; then
  echo "HDD temperature monitoring is available (hddtemp)"
  STORAGE_TOOLS_FOUND=true
fi

# Check NVMe tools
if command -v nvme &> /dev/null; then
  echo "NVMe SSD monitoring is available (nvme-cli)"
  STORAGE_TOOLS_FOUND=true
fi

# Check smartmontools
if command -v smartctl &> /dev/null; then
  echo "SMART monitoring is available (smartmontools)"
  STORAGE_TOOLS_FOUND=true
fi

if [ "$STORAGE_TOOLS_FOUND" = false ]; then
  echo "No storage monitoring tools found. Storage temperature will be unavailable."
  echo "Install with: sudo apt-get install smartmontools nvme-cli"
  echo "Disk usage percentage will be shown instead."
fi

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
  echo "NVIDIA GPU detected. GPU monitoring will be available."
else
  echo "NVIDIA GPU tools not found. GPU monitoring may be limited."
fi

# Check network connectivity
echo "Checking network connectivity..."
if ! ping -c 1 -W 2 app.divoom-gz.com &>/dev/null; then
  echo "Warning: Unable to reach Divoom server (app.divoom-gz.com)"
  echo "This may affect device discovery. Check your internet connection."
else
  echo "Divoom server is reachable. Device discovery should work correctly."
fi

# Make the Python script executable
chmod +x divoom_monitor.py

# Debug mode
if [ "$1" == "--debug" ]; then
  echo "Running in debug mode..."
  python3 -u divoom_monitor.py
elif [ "$1" == "--restart" ]; then
  echo "Running with auto-restart on failure..."
  while true; do
    python3 divoom_monitor.py
    echo "Program exited. Restarting in 5 seconds..."
    sleep 5
  done
else
  # Run the application
  python3 divoom_monitor.py
fi

# Exit gracefully
exit 0 