#!/usr/bin/env python3
"""
Divoom Linux Monitor Tool
A native Linux tool for sending system information to Divoom devices
"""

import os
import sys
import time
import json
import signal
import threading
import subprocess
import requests
from datetime import datetime

class DivoomMonitor:
    def __init__(self):
        self.device_ip = None
        self.selected_lcd_id = 0
        self.running = True
        self.update_thread = None
        self.device_id = None
        self.device_hardware = None
        self.lcd_independence = 0
        
    def start(self):
        """Start the monitor application"""
        print("Divoom Linux Monitor Tool")
        print("-------------------------")
        
        # Register signal handler for clean exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Discover Divoom devices
        self.update_device_list()
        
        if not self.device_ip:
            print("No device selected. Exiting.")
            return
            
        # Select PC Monitor Clock
        self.select_pc_monitor_clock()
            
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Main input loop
        print("\nPress 'r' to refresh device list")
        print("Press 'q' to quit\n")
        
        while self.running:
            try:
                key = input()
                if key.lower() == 'r':
                    self.update_device_list()
                    if self.device_ip:
                        self.select_pc_monitor_clock()
                elif key.lower() == 'q':
                    self.running = False
            except EOFError:
                self.running = False
        
        print("\nShutting down...")
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C"""
        self.running = False
        print("\nShutting down...")
        sys.exit(0)
    
    def update_device_list(self):
        """Find Divoom devices on the network using the Divoom API"""
        print("Searching for Divoom devices on the network...")
        
        try:
            response = requests.get("http://app.divoom-gz.com/Device/ReturnSameLANDevice", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                if 'DeviceList' in data and data['DeviceList']:
                    print("\nFound devices:")
                    for i, device in enumerate(data['DeviceList']):
                        print(f"{i+1}. {device['DeviceName']} - {device['DevicePrivateIP']}")
                    
                    try:
                        selection = int(input("\nSelect device number: "))
                        if 1 <= selection <= len(data['DeviceList']):
                            selected_device = data['DeviceList'][selection-1]
                            self.device_ip = selected_device['DevicePrivateIP']
                            self.device_id = selected_device.get('DeviceId', '0')
                            self.device_hardware = selected_device.get('Hardware', 0)
                            print(f"Selected device: {selected_device['DeviceName']} at {self.device_ip}")
                            
                            # For TimeGate (Hardware==400) or devices with multiple screens, 
                            # allow selection of the LCD screen
                            if self.device_hardware == 400:
                                print("\nThis appears to be a TimeGate device with multiple screens.")
                                try:
                                    max_screens = 5  # TimeGate typically has 5 screens
                                    print(f"Select screen (1-{max_screens}):")
                                    for i in range(max_screens):
                                        print(f"{i+1}. Screen {i+1}")
                                    
                                    screen_selection = int(input("\nSelect screen number: "))
                                    if 1 <= screen_selection <= max_screens:
                                        # Screen ID is 0-based in the API
                                        self.selected_lcd_id = screen_selection - 1
                                        print(f"Selected screen {screen_selection}")
                                    else:
                                        print("Invalid screen selection. Using screen 1.")
                                        self.selected_lcd_id = 0
                                except ValueError:
                                    print("Invalid input. Using screen 1.")
                                    self.selected_lcd_id = 0
                            else:
                                # For non-TimeGate devices, default to screen 0
                                self.selected_lcd_id = 0
                                print("Using default screen for this device.")
                                
                            return
                        else:
                            print("Invalid selection")
                    except ValueError:
                        print("Invalid input")
                else:
                    print("No devices found")
            else:
                print(f"Error: HTTP {response.status_code}")
        except Exception as e:
            print(f"Error finding devices: {e}")
    
    def select_pc_monitor_clock(self):
        """Select the PC Monitor Clock on the device"""
        if not self.device_ip:
            return
            
        print("Setting up PC Monitor Clock on device...")
        
        # For TimeGate devices (Hardware == 400), get LCD independence
        if self.device_hardware == 400:
            try:
                url = f"http://app.divoom-gz.com/Channel/Get5LcdInfoV2?DeviceType=LCD&DeviceId={self.device_id}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200 and response.text:
                    data = response.json()
                    if 'LcdIndependence' in data:
                        self.lcd_independence = data['LcdIndependence']
                        print(f"Device has LCD independence: {self.lcd_independence}")
                        print(f"Using screen {self.selected_lcd_id + 1}")
            except Exception as e:
                print(f"Error getting LCD info: {e}")
        
        # Select the PC Monitor Clock (Clock ID 625)
        max_retries = 3
        retry_count = 0
        success = False
        
        while not success and retry_count < max_retries:
            try:
                payload = {
                    "Command": "Channel/SetClockSelectId", 
                    "LcdIndependence": self.lcd_independence,
                    "LcdIndex": self.selected_lcd_id,
                    "ClockId": 625
                }
                
                print(f"Selecting PC Monitor Clock with payload: {json.dumps(payload)}")
                
                response = self.http_post(f"http://{self.device_ip}:80/post", payload)
                print(f"Clock selection response: {response}")
                
                if "Error" not in response and "HTTP Error" not in response:
                    success = True
                    print("PC Monitor Clock selected successfully!")
                else:
                    retry_count += 1
                    print(f"Failed to select PC Monitor Clock, retrying ({retry_count}/{max_retries})...")
                    time.sleep(2)  # Wait before retrying
            except Exception as e:
                retry_count += 1
                print(f"Error selecting PC Monitor Clock: {e}, retrying ({retry_count}/{max_retries})...")
                time.sleep(2)  # Wait before retrying
                
        # Give the device time to switch to the PC Monitor Clock
        time.sleep(2)
        
        if not success:
            print("Warning: Failed to select PC Monitor Clock after multiple attempts.")
            print("The device might not display system information correctly.")
            print("You can try pressing 'r' to refresh the device connection.")
            
    def http_post(self, url, data):
        """Send HTTP POST request to the device API"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Convert to JSON string
            json_data = json.dumps(data)
            
            # Print debug info for troubleshooting
            debug_info = f"POST Request to {url}\nPayload: {json_data}"
            print(f"\r{debug_info}", end='')
            
            # Use requests.post with the data parameter as a string
            response = requests.post(
                url,
                data=json_data,
                headers=headers,
                timeout=3
            )
            
            if response.status_code == 200:
                try:
                    # Try to parse as JSON to validate response
                    if response.text:
                        json.loads(response.text)
                    return response.text or "Success (empty response)"
                except:
                    return "Success (non-JSON response)"
            else:
                return f"HTTP Error: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return f"Connection Error: Unable to connect to {url}"
        except requests.exceptions.Timeout:
            return f"Timeout Error: Request to {url} timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def update_loop(self):
        """Continuously update hardware info to the device"""
        consecutive_failures = 0
        max_failures = 5
        
        while self.running:
            try:
                success = self.send_hardware_info()
                
                if success:
                    consecutive_failures = 0  # Reset failure counter on success
                else:
                    consecutive_failures += 1
                    
                # If we've had too many consecutive failures, try to reconnect
                if consecutive_failures >= max_failures:
                    print("\nToo many consecutive failures. Attempting to reconnect...")
                    if self.device_ip:
                        # Try to select the PC Monitor Clock again
                        self.select_pc_monitor_clock()
                        consecutive_failures = 0  # Reset counter
                
                time.sleep(2)  # Update interval
            except Exception as e:
                print(f"\rError updating: {e}", end='')
                consecutive_failures += 1
                time.sleep(5)
    
    def send_hardware_info(self):
        """Send hardware information to the Divoom device"""
        if not self.device_ip:
            return False
            
        # Default values
        cpu_temp = "--"
        cpu_use = "--"
        gpu_temp = "--"
        gpu_use = "--"
        mem_use = "--"
        storage_info = "--"  # Storage temperature or usage
        
        # Get CPU usage
        try:
            cpu_use_val = self.get_cpu_usage()
            cpu_use = f"{cpu_use_val}%"
            if len(cpu_use) > 3:  # Keep display format consistent
                cpu_use = cpu_use[:3]
        except Exception:
            pass
            
        # Get CPU temperature
        try:
            cpu_temp_val = self.get_cpu_temperature()
            if cpu_temp_val:
                cpu_temp = f"{cpu_temp_val}C"
        except Exception:
            pass
            
        # Get memory usage
        try:
            mem_use_val = self.get_memory_usage()
            mem_use = f"{mem_use_val}%"
            if len(mem_use) > 3:  # Keep display format consistent
                mem_use = mem_use[:3]
        except Exception:
            pass
            
        # Get GPU info if available
        try:
            gpu_info = self.get_gpu_info()
            if gpu_info:
                if 'temp' in gpu_info:
                    gpu_temp = f"{gpu_info['temp']}C"
                if 'usage' in gpu_info:
                    gpu_use = f"{gpu_info['usage']}%"
                    if len(gpu_use) > 3:  # Keep display format consistent
                        gpu_use = gpu_use[:3]
        except Exception:
            pass
            
        # Get storage information (temp for HDD or usage for SSD)
        try:
            # First try to get temperature
            storage_temp = self.get_storage_temperature()
            if storage_temp:
                storage_info = f"{storage_temp}C"
            else:
                # If temperature not available, try to get usage percentage
                storage_usage = self.get_storage_usage()
                if storage_usage:
                    storage_info = f"{storage_usage}%"
        except Exception:
            pass
            
        # Prepare JSON payload
        # Data order: CPU usage, GPU usage, CPU temp, GPU temp, Memory usage, Storage info
        payload = {
            "Command": "Device/UpdatePCParaInfo",
            "ScreenList": [
                {
                    "LcdId": self.selected_lcd_id,
                    "DispData": [
                        cpu_use,      # CPU Usage
                        gpu_use,      # GPU Usage
                        cpu_temp,     # CPU Temp
                        gpu_temp,     # GPU Temp
                        mem_use,      # Memory Usage
                        storage_info  # Storage Temp or Usage
                    ]
                }
            ]
        }
        
        # Send to device using our HTTP post method
        response = self.http_post(f"http://{self.device_ip}:80/post", payload)
        if "Error" not in response and "HTTP Error" not in response:
            print(f"\rSent update to screen {self.selected_lcd_id+1}: CPU: {cpu_use}/{cpu_temp}, GPU: {gpu_use}/{gpu_temp}, MEM: {mem_use}, STORAGE: {storage_info}", end='')
            return True
        else:
            print(f"\r{response}", end='')
            return False
    
    def get_cpu_usage(self):
        """Get CPU usage percentage using Linux native tools"""
        command = "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'"
        output = subprocess.check_output(command, shell=True).decode('utf-8').strip()
        return round(float(output))
    
    def get_cpu_temperature(self):
        """Get CPU temperature using lm_sensors or system files"""
        # Try with lm_sensors first
        try:
            output = subprocess.check_output("sensors | grep 'Core 0' | awk '{print $3}' | sed 's/+\\(.*\\)°C/\\1/'", shell=True).decode('utf-8').strip()
            if output:
                return round(float(output.replace(',', '.')))
        except:
            pass
            
        # Fallback to system file (common on many Linux systems)
        try:
            temp_files = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/devices/platform/coretemp.0/temp1_input'
            ]
            
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        temp = int(f.read().strip()) / 1000
                        return round(temp)
        except:
            pass
            
        return None
    
    def get_memory_usage(self):
        """Get memory usage percentage from /proc/meminfo"""
        with open('/proc/meminfo', 'r') as f:
            mem_info = f.read()
            
        total = 0
        available = 0
        
        for line in mem_info.splitlines():
            if line.startswith('MemTotal:'):
                total = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                available = int(line.split()[1])
                
        if total > 0 and available > 0:
            usage = (total - available) * 100 // total
            return usage
            
        return 0
    
    def get_gpu_info(self):
        """Get GPU information for NVIDIA GPUs"""
        # Try NVIDIA GPU
        try:
            # Check if nvidia-smi is available
            if subprocess.call("which nvidia-smi > /dev/null", shell=True) == 0:
                # Get temperature
                temp_output = subprocess.check_output("nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader", shell=True).decode('utf-8').strip()
                # Get utilization
                use_output = subprocess.check_output("nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader", shell=True).decode('utf-8').strip()
                
                return {
                    'temp': int(temp_output),
                    'usage': int(use_output.replace('%', ''))
                }
        except:
            pass
            
        # AMD GPU support could be added here
        # This would require implementation specific to AMD hardware
            
        return None
    
    def get_storage_temperature(self):
        """Get storage temperature with multi-method approach for different storage types"""
        # Try hddtemp for traditional HDDs
        try:
            if subprocess.call("which hddtemp > /dev/null", shell=True) == 0:
                # Get the first disk
                disks = subprocess.check_output("lsblk -d -o NAME | grep -v NAME", shell=True).decode('utf-8').strip().split('\n')
                for disk in disks:
                    try:
                        # Try to get temperature, but don't fail if one disk doesn't support it
                        output = subprocess.check_output(f"sudo hddtemp /dev/{disk} 2>/dev/null | cut -d: -f3 | sed 's/°C//'", 
                                                        shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                        if output and output != "":
                            return int(float(output))
                    except:
                        continue
        except:
            pass
            
        # Try nvme-cli for NVMe SSDs
        try:
            if subprocess.call("which nvme > /dev/null", shell=True) == 0:
                # Find NVMe devices
                nvme_disks = subprocess.check_output("find /dev -name 'nvme[0-9]' | sort", 
                                                    shell=True).decode('utf-8').strip().split('\n')
                for disk in nvme_disks:
                    if disk:  # Skip empty lines
                        try:
                            # Get temperature from NVMe smart log
                            output = subprocess.check_output(f"sudo nvme smart-log {disk} 2>/dev/null | grep temperature | head -n1 | awk '{{print $3}}'",
                                                            shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                            if output and output.isdigit():
                                # NVMe temps are often in Kelvin, convert to Celsius
                                temp = int(output)
                                if temp > 273:  # If Kelvin
                                    temp = temp - 273
                                return temp
                        except:
                            continue
        except:
            pass
            
        # Try smartctl as a fallback for any drive
        try:
            if subprocess.call("which smartctl > /dev/null", shell=True) == 0:
                disks = subprocess.check_output("lsblk -d -o NAME | grep -v NAME", shell=True).decode('utf-8').strip().split('\n')
                for disk in disks:
                    try:
                        output = subprocess.check_output(f"sudo smartctl -A /dev/{disk} 2>/dev/null | grep -i temperature | head -n1 | awk '{{print $10}}'",
                                                        shell=True, stderr=subprocess.DEVNULL).decode('utf-8').strip()
                        if output and output.isdigit():
                            return int(output)
                    except:
                        continue
        except:
            pass
            
        return None
    
    def get_storage_usage(self):
        """Get storage usage percentage for the root filesystem"""
        try:
            # Get usage of the root filesystem
            output = subprocess.check_output("df -h / | awk 'NR==2 {print $5}' | sed 's/%//'", 
                                            shell=True).decode('utf-8').strip()
            if output and output.isdigit():
                return int(output)
        except:
            pass
            
        return None

if __name__ == "__main__":
    monitor = DivoomMonitor()
    monitor.start() 