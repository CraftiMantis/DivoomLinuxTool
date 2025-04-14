# Divoom Timesgate PC Monitor - Linux

A native Linux tool for sending system information to Divoom TimeGate device.

## Getting Started

### Quick Start (Recommended)

For the easiest setup:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/DivoomLinuxTool.git

# 2. Navigate to the directory
cd DivoomLinuxTool

# 3. Make setup and run scripts executable (if needed)
chmod +x setup.sh run.sh

# 4. Run the setup script to install all dependencies
sudo ./setup.sh

# 5. Run the application
sudo ./run.sh
```

### Prerequisites

- Ubuntu or another Debian-based Linux distribution
- Python 3.6 or higher
- Required packages (automatically installed by setup.sh):
  - `lm-sensors` (for CPU temperature monitoring)
  - `hddtemp`, `smartmontools` and `nvme-cli` (for storage monitoring)

### Manual Installation

If you prefer to install dependencies manually:

```bash
# 1. Update package list
sudo apt-get update

# 2. Install Python and required packages
sudo apt-get install -y python3 python3-pip lm-sensors hddtemp smartmontools nvme-cli

# 3. Configure sensors
sudo sensors-detect --auto
sudo service kmod start

# 4. Install Python dependencies
sudo pip3 install requests

# 5. Make scripts executable
chmod +x run.sh src/divoom_monitor.py
```

## Running the Application

After completing either the quick setup or manual installation:

```bash
# Run the application (with root permissions for better hardware monitoring)
sudo ./run.sh

# Or run with debug output (shows all HTTP requests)
sudo ./run.sh --debug

# Run with auto-restart if the program crashes
sudo ./run.sh --restart
```

## Usage

1. Run the application as shown above
2. The tool will search for Divoom devices on your local network
3. Select a device from the list by entering its number
4. For TimeGate devices, you will be prompted to select which screen to use (1-5)
5. The tool will automatically select the PC Monitor Clock on your device
6. System information will be sent to the selected device/screen
7. Press 'r' to refresh the device list
8. Press 'q' to quit

## TimeGate Devices

TimeGates device with multiple screens:

1. When you select the device, you'll be prompted to choose which screen (1-5) to use
2. Each screen on the TimeGate can be controlled independently
3. The tool will remember your screen selection while running
4. To change screens, press 'r' to refresh the device list and select again

## Storage Monitoring

The tool intelligently monitors storage devices:

- For traditional HDDs: Shows temperature via `hddtemp`
- For NVMe SSDs: Shows temperature via `nvme-cli`
- For other SSDs: Attempts to use SMART monitoring via `smartctl`
- As a fallback: Shows storage usage percentage when temperature isn't available

This ensures that both traditional hard drives and modern SSDs are properly supported.

## Latest Improvements

- Advanced screen selection for TimeGate devices with multiple screens
- Comprehensive support for SSDs and modern storage devices
- Optimized communication with Divoom devices
- Intelligent PC Monitor Clock selection functionality
- Improved error handling and diagnostics
- Automatic reconnection if device connection is lost
- Network connectivity checks
- Auto-restart mode for maximum reliability
- Optimized JSON payload formatting for device compatibility

## Permissions

Some hardware monitoring features require root privileges:
- CPU temperature sensors
- GPU monitoring 
- Storage monitoring (especially for NVMe and SMART data)

For the best experience, run the application with sudo:

```bash
sudo ./run.sh
```

## Troubleshooting

- If hardware information isn't displaying correctly, make sure you have the necessary permissions
- For GPU temperature monitoring:
  - NVIDIA: Ensure nvidia-smi is available (install nvidia drivers)
  - AMD: Currently limited support
- For storage monitoring:
  - HDDs: Install hddtemp (`sudo apt install hddtemp`)
  - NVMe SSDs: Install nvme-cli (`sudo apt install nvme-cli`)
  - Other SSDs: Install smartmontools (`sudo apt install smartmontools`)
- If devices aren't found, check that your Divoom device is on the same network as your computer
- If device communication fails, try refreshing the device list ('r')
- For TimeGate devices, ensure you select the correct screen number (1-5)
- If you experience connection issues:
  1. Make sure your firewall allows outbound connections on port 80
  2. Try using the auto-restart mode: `sudo ./run.sh --restart`
  3. Verify your device's firmware is up to date

## Notes

This is a native Linux implementation that uses:

- Linux system tools (lm_sensors, nvme-cli, smartmontools, /proc/meminfo) for hardware monitoring
- Python for maximum compatibility across Linux distributions
- HTTP requests to communicate directly with Divoom devices 
