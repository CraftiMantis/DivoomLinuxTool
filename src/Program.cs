using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.IO;
using Newtonsoft.Json;
using LibreHardwareMonitor.Hardware;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace DivoomLinuxTool
{
    class Program
    {
        private static Computer? computer;
        private static UpdateVisitor? updateVisitor;
        private static string? deviceIPAddr;
        private static int selectedLCDID = 0;
        private static HttpClient httpClient = new HttpClient();
        private static Timer? statusUpdateTimer;
        private static bool isRunning = true;
        
        static async Task Main(string[] args)
        {
            Console.WriteLine("Divoom Linux Monitor Tool");
            Console.WriteLine("-------------------------");

            // Initialize hardware monitor
            computer = new Computer
            {
                IsCpuEnabled = true,
                IsGpuEnabled = true,
                IsMemoryEnabled = true,
                IsStorageEnabled = true
            };
            
            updateVisitor = new UpdateVisitor();
            computer.Open();
            
            // Search for Divoom devices on the network
            await UpdateDeviceListAsync();
            
            // Setup timer for regular updates
            statusUpdateTimer = new Timer(async _ => await SendHardwareInfoAsync(), null, 0, 1000);
            
            // Handle console input for basic controls
            Console.WriteLine("\nPress 'r' to refresh device list");
            Console.WriteLine("Press 'q' to quit\n");
            
            while (isRunning)
            {
                var key = Console.ReadKey(true);
                switch (key.KeyChar)
                {
                    case 'r':
                        await UpdateDeviceListAsync();
                        break;
                    case 'q':
                        isRunning = false;
                        break;
                }
            }
            
            // Cleanup
            statusUpdateTimer?.Dispose();
            computer.Close();
        }
        
        private static async Task UpdateDeviceListAsync()
        {
            Console.WriteLine("Searching for Divoom devices on the network...");
            
            try
            {
                string url = "http://app.divoom-gz.com/Device/ReturnSameLANDevice";
                string response = await httpClient.GetStringAsync(url);
                
                var deviceList = JsonConvert.DeserializeObject<DivoomDeviceList>(response);
                
                if (deviceList?.DeviceList != null && deviceList.DeviceList.Length > 0)
                {
                    Console.WriteLine("\nFound devices:");
                    for (int i = 0; i < deviceList.DeviceList.Length; i++)
                    {
                        Console.WriteLine($"{i + 1}. {deviceList.DeviceList[i].DeviceName} - {deviceList.DeviceList[i].DevicePrivateIP}");
                    }
                    
                    Console.Write("\nSelect device number: ");
                    if (int.TryParse(Console.ReadLine(), out int selection) && selection > 0 && selection <= deviceList.DeviceList.Length)
                    {
                        deviceIPAddr = deviceList.DeviceList[selection - 1].DevicePrivateIP;
                        Console.WriteLine($"Selected device: {deviceList.DeviceList[selection - 1].DeviceName} at {deviceIPAddr}");
                        
                        // For simplicity, we're using LCD index 0
                        selectedLCDID = 0;
                    }
                    else
                    {
                        Console.WriteLine("Invalid selection");
                    }
                }
                else
                {
                    Console.WriteLine("No devices found");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error finding devices: {ex.Message}");
            }
        }
        
        private static async Task SendHardwareInfoAsync()
        {
            if (string.IsNullOrEmpty(deviceIPAddr))
                return;
                
            string cpuTemp = "--", cpuUse = "--", gpuTemp = "--", gpuUse = "--", 
                   memUse = "--", diskUse = "--";
            
            try
            {
                computer?.Accept(updateVisitor);
                
                foreach (var hardware in computer?.Hardware ?? Array.Empty<IHardware>())
                {
                    if (hardware.HardwareType == HardwareType.Cpu)
                    {
                        foreach (var sensor in hardware.Sensors)
                        {
                            if (sensor.SensorType == SensorType.Temperature)
                            {
                                cpuTemp = sensor.Value?.ToString("0") + "C";
                            }
                            else if (sensor.SensorType == SensorType.Load)
                            {
                                cpuUse = sensor.Value?.ToString("0") + "%";
                            }
                        }
                    }
                    else if (hardware.HardwareType == HardwareType.GpuNvidia || 
                             hardware.HardwareType == HardwareType.GpuAmd)
                    {
                        foreach (var sensor in hardware.Sensors)
                        {
                            if (sensor.SensorType == SensorType.Temperature)
                            {
                                gpuTemp = sensor.Value?.ToString("0") + "C";
                            }
                            else if (sensor.SensorType == SensorType.Load)
                            {
                                gpuUse = sensor.Value?.ToString("0") + "%";
                            }
                        }
                    }
                    else if (hardware.HardwareType == HardwareType.Storage)
                    {
                        foreach (var sensor in hardware.Sensors)
                        {
                            if (sensor.SensorType == SensorType.Temperature)
                            {
                                diskUse = sensor.Value?.ToString("0") + "C";
                                break;
                            }
                        }
                    }
                }
                
                // Get memory usage from /proc/meminfo on Linux
                if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                {
                    var memInfo = File.ReadAllText("/proc/meminfo");
                    var memTotal = ParseMemInfo(memInfo, "MemTotal:");
                    var memAvailable = ParseMemInfo(memInfo, "MemAvailable:");
                    
                    if (memTotal > 0 && memAvailable > 0)
                    {
                        var memUsage = (int)((memTotal - memAvailable) * 100 / memTotal);
                        memUse = memUsage.ToString() + "%";
                    }
                }
                
                var postData = new
                {
                    Command = "Device/UpdatePCParaInfo",
                    ScreenList = new[]
                    {
                        new
                        {
                            LcdId = selectedLCDID,
                            DispData = new[]
                            {
                                cpuUse,   // CPU Usage
                                gpuUse,   // GPU Usage
                                cpuTemp,  // CPU Temp
                                gpuTemp,  // GPU Temp
                                memUse,   // Memory Usage
                                diskUse   // Disk Temp
                            }
                        }
                    }
                };
                
                string json = JsonConvert.SerializeObject(postData);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                var response = await httpClient.PostAsync($"http://{deviceIPAddr}:80/post", content);
                if (response.IsSuccessStatusCode)
                {
                    Console.Write($"\rSent update: CPU: {cpuUse}/{cpuTemp}, GPU: {gpuUse}/{gpuTemp}, MEM: {memUse}, DISK: {diskUse}");
                }
            }
            catch (Exception)
            {
                // Silent failure
            }
        }
        
        private static long ParseMemInfo(string memInfo, string key)
        {
            var lines = memInfo.Split('\n');
            foreach (var line in lines)
            {
                if (line.StartsWith(key))
                {
                    var parts = line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    if (parts.Length >= 2 && long.TryParse(parts[1], out long value))
                    {
                        return value;
                    }
                }
            }
            return 0;
        }
    }

    public class UpdateVisitor : IVisitor
    {
        public void VisitComputer(IComputer computer)
        {
            computer.Traverse(this);
        }

        public void VisitHardware(IHardware hardware)
        {
            hardware.Update();
            foreach (var subHardware in hardware.SubHardware)
            {
                subHardware.Accept(this);
            }
        }

        public void VisitSensor(ISensor sensor) { }

        public void VisitParameter(IParameter parameter) { }
    }
    
    public class DivoomDeviceItem
    {
        public string DeviceName { get; set; } = "";
        public string DeviceId { get; set; } = "";
        public string DeviceMac { get; set; } = "";
        public string DevicePrivateIP { get; set; } = "";
    }
    
    public class DivoomDeviceList
    {
        public DivoomDeviceItem[]? DeviceList { get; set; }
    }
} 