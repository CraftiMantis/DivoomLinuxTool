# Divoom Linux Monitor Tool

A native Linux implementation for sending system information to Divoom Pixoo64 and TimeGate devices.

![Divoom Device](https://i.imgur.com/fMUQk9p.jpg)

## Overview

This project provides a native Linux solution for displaying system metrics (CPU, GPU, memory usage, temperatures) on Divoom devices. Designed specifically for Ubuntu and other Linux distributions, it leverages the power of native Linux tools for hardware monitoring.

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

See the [README.md](./README.md) for detailed installation and usage instructions.

## Features

- **Native Linux Design**: Built with Python using native Linux system tools
- **Multi-Device Support**: Compatible with Pixoo64, TimeGate, and other Divoom devices
- **Screen Selection**: Full support for TimeGate devices with multiple screens
- **Auto-Recovery**: Automatically reconnects to the device if connection is lost
- **Advanced Hardware Monitoring**: Captures system metrics using Linux's built-in tools
- **Comprehensive Storage Support**: Handles both traditional HDDs and modern SSDs for storage information
- **Debug Mode**: Detailed logging for troubleshooting
- **Auto-Restart Mode**: Automatically restarts if the application crashes

## Implementation Details

### Architecture

The tool is implemented in Python using a modular design with these key components:

1. **Device Discovery**: Uses the Divoom API to find devices on the local network
2. **Clock Selection**: Configures the device to display the PC Monitor Clock
3. **Hardware Monitoring**: Collects system metrics using Linux-native tools
4. **Data Transmission**: Sends formatted system metrics to the device
5. **Connection Management**: Handles reconnections and error recovery

### Key Technologies

- **Python 3**: Core programming language
- **requests**: HTTP library for API communication
- **lm_sensors**: Hardware monitoring for temperatures
- **smartmontools & nvme-cli**: Storage monitoring for both HDDs and SSDs
- **subprocess**: System command execution for metrics collection
- **threading**: Background processing for continuous updates

### API Implementation

The tool interacts with the Divoom API through HTTP requests:

1. **Device Discovery**: `GET http://app.divoom-gz.com/Device/ReturnSameLANDevice`
2. **Clock Selection**: `POST http://{device_ip}/post` with `Channel/SetClockSelectId` command
3. **Data Updates**: `POST http://{device_ip}/post` with `Device/UpdatePCParaInfo` command

### Hardware Monitoring

System metrics are collected using native Linux tools:

- **CPU Usage**: Parsed from `top` command
- **CPU Temperature**: Read from `lm-sensors` or system files
- **Memory Usage**: Parsed from `/proc/meminfo`
- **GPU Information**: Collected from `nvidia-smi` (for NVIDIA GPUs)
- **Storage Information**:
  - **HDD Temperature**: Read from `hddtemp`
  - **SSD Temperature**: Read from `nvme-cli` or `smartctl`
  - **Storage Usage**: Falls back to disk usage percentage when temperature unavailable

## Code Structure

```
DivoomLinuxTool/
├── src/
│   └── divoom_monitor.py    # Main implementation
├── run.sh                   # Shell script for running the tool
├── setup.sh                 # Dependency installation script
└── README.md                # Usage instructions
```

### Key Classes and Methods

- **DivoomMonitor**: Main class that handles all functionality
  - `update_device_list()`: Discovers Divoom devices on the network
  - `select_pc_monitor_clock()`: Sets up the PC Monitor Clock
  - `send_hardware_info()`: Collects and sends system information
  - `http_post()`: Implementation for API communication
  - `get_cpu_usage()`, `get_cpu_temperature()`: Hardware metric collection
  - `get_storage_temperature()`: Multi-method storage temperature detection
  - `get_storage_usage()`: Filesystem usage monitoring

## Linux Implementation Advantages

| Feature | Linux Implementation Advantage |
|---------|--------------------------------|
| Hardware Monitoring | Uses native Linux tools for accurate data |
| Storage Support | Multiple methods for both HDD and SSD temperature monitoring |
| Memory Info | Direct access to Linux /proc filesystem for accurate memory stats |
| Error Handling | Advanced auto-recovery and reconnection |
| Multi-screen Support | Guided selection with prompts for TimeGate devices |
| Resource Usage | Lightweight implementation without GUI overhead |

## Development Considerations

### Challenges Addressed

1. **API Communication**: Implemented precise HTTP handling to match Divoom API requirements
2. **Error Recovery**: Added auto-reconnection to handle network issues
3. **Screen Selection**: Implemented TimeGate multi-screen support
4. **SSD Support**: Added multiple methods to monitor modern storage devices
5. **Hardware Diversity**: Support for various CPU/GPU/storage configurations

### Future Enhancements

- Add support for AMD GPU monitoring
- Create a simple GUI using PyQt or similar
- Add support for additional Divoom device features
- Implement more advanced hardware monitoring for specialized hardware

## Installation and Usage

See [README.md](./README.md) for detailed installation and usage instructions.

## License

[MIT License](./LICENSE)

## Credits

- Created by [Your Name]
- Developed for the Linux community 