/*
 * Stow WMS Mobile Racking TCP-IP Communication Example (C#)
 * Based on official Stow documentation and examples
 * 
 * Protocol Format (from PDF documentation):
 * - Status Request: Send (0, 2) → Receive 20 bytes
 * - Open Aisle: Send (aisle_number, 1) → Receive 20 bytes
 * - All data in little-endian format
 */

using System;
using System.Net.Sockets;
using System.Linq;

namespace StowMobileRacking
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== Stow Mobile Racking Communication Test ===");
            
            try
            {
                using (var client = new TcpClient())
                {
                    // Connect to Mobile Racking system
                    client.ReceiveTimeout = 5000; // 5 second timeout
                    client.Connect("1.1.1.2", 2000);
                    
                    Console.WriteLine("✅ Connected to Mobile Racking at 1.1.1.2:2000");
                    
                    using (var stream = client.GetStream())
                    {
                        var mobileComm = new StowMobileComm(stream);
                        
                        // Test 1: Request status (0, 2)
                        Console.WriteLine("\n📊 Testing Status Request...");
                        var statusResponse = mobileComm.RequestStatus();
                        if (statusResponse != null)
                        {
                            Console.WriteLine($"Status Response: {statusResponse}");
                        }
                        else
                        {
                            Console.WriteLine("❌ No status response received");
                        }
                        
                        // Test 2: Open aisle 1 (1, 1)
                        Console.WriteLine("\n🚪 Testing Open Aisle 1...");
                        var aisleResponse = mobileComm.OpenAisle(1);
                        if (aisleResponse != null)
                        {
                            Console.WriteLine($"Aisle Response: {aisleResponse}");
                        }
                        else
                        {
                            Console.WriteLine("❌ No aisle response received");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Error: {ex.Message}");
            }
            
            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }
    }
    
    public class StowMobileComm
    {
        private NetworkStream stream;
        
        public StowMobileComm(NetworkStream networkStream)
        {
            stream = networkStream;
        }
        
        public MobileResponse RequestStatus()
        {
            // Send status request: (0, 2) according to PDF specification
            return Transmit(0, 2, "Status Request");
        }
        
        public MobileResponse OpenAisle(byte aisleNumber)
        {
            // Send open aisle command: (aisle_number, 1) according to PDF specification
            if (aisleNumber < 1 || aisleNumber > 19)
                throw new ArgumentException("Aisle number must be between 1 and 19");
                
            return Transmit(aisleNumber, 1, $"Open Aisle {aisleNumber}");
        }
        
        private MobileResponse Transmit(byte byte1, byte byte2, string description)
        {
            try
            {
                // Prepare command according to PDF specification
                byte[] command = new byte[4];
                BitConverter.GetBytes((ushort)byte1).CopyTo(command, 0);
                BitConverter.GetBytes((ushort)byte2).CopyTo(command, 2);
                
                // Send command
                stream.Write(command, 0, command.Length);
                Console.WriteLine($"📤 Sent {description}: {string.Join(" ", command.Select(b => b.ToString("X2")))}");
                
                // Read response
                byte[] responseBuffer = new byte[MobileResponse.ResponseLength];
                int bytesRead = stream.Read(responseBuffer, 0, responseBuffer.Length);
                
                if (bytesRead == MobileResponse.ResponseLength)
                {
                    Console.WriteLine($"📥 Received {bytesRead} bytes: {string.Join(" ", responseBuffer.Select(b => b.ToString("X2")))}");
                    return new MobileResponse(responseBuffer);
                }
                else
                {
                    Console.WriteLine($"⚠️ Expected {MobileResponse.ResponseLength} bytes, got {bytesRead}");
                    return null;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Communication error: {ex.Message}");
                return null;
            }
        }
    }
    
    public class MobileResponse
    {
        public const int ResponseLength = 20;
        
        // Status properties based on Mobile Racking protocol
        public bool CanOpen { get; private set; }
        public bool ReadyToOperate { get; private set; }
        public bool ManualMode { get; private set; }
        public bool PowerOn { get; private set; }
        public bool AutomaticModeOn { get; private set; }
        public bool NightMode { get; private set; }
        public bool Moving { get; private set; }
        public bool LightingOn { get; private set; }
        public ushort MobileQuantity { get; private set; }
        public ushort Position1 { get; private set; }
        
        private byte[] rawData;
        
        public MobileResponse(byte[] data)
        {
            if (data == null || data.Length != ResponseLength)
                throw new ArgumentException($"MobileResponse requires exactly {ResponseLength} bytes");
                
            rawData = new byte[data.Length];
            Array.Copy(data, rawData, data.Length);
            
            // Handle endianness - Mobile Racking uses little-endian
            if (!BitConverter.IsLittleEndian)
            {
                // Convert from big-endian to little-endian
                for (int i = 0; i < data.Length; i += 2)
                {
                    Array.Reverse(rawData, i, 2);
                }
            }
            
            // Parse status fields (each field is 2 bytes / 16-bit word)
            CanOpen = BitConverter.ToUInt16(rawData, 0) == 1;
            ReadyToOperate = BitConverter.ToUInt16(rawData, 2) == 1;
            ManualMode = BitConverter.ToUInt16(rawData, 4) == 1;
            PowerOn = BitConverter.ToUInt16(rawData, 6) == 1;
            AutomaticModeOn = BitConverter.ToUInt16(rawData, 8) == 1;
            NightMode = BitConverter.ToUInt16(rawData, 10) == 1;
            Moving = BitConverter.ToUInt16(rawData, 12) == 1;
            LightingOn = BitConverter.ToUInt16(rawData, 14) == 1;
            MobileQuantity = BitConverter.ToUInt16(rawData, 16);
            Position1 = BitConverter.ToUInt16(rawData, 18);
        }
        
        public override string ToString()
        {
            return $"Power: {(PowerOn ? "ON" : "OFF")}, " +
                   $"Mode: {(AutomaticModeOn ? "AUTO" : ManualMode ? "MANUAL" : "UNKNOWN")}, " +
                   $"Ready: {(ReadyToOperate ? "YES" : "NO")}, " +
                   $"Can Open: {(CanOpen ? "YES" : "NO")}, " +
                   $"Mobiles: {MobileQuantity}, " +
                   $"Position: {Position1}";
        }
        
        public string GetRawDataHex()
        {
            return string.Join(" ", rawData.Select(b => b.ToString("X2")));
        }
    }
}

/*
 * Compilation Instructions:
 * ========================
 * 
 * 1. Save this file as: StowMobileRacking.cs
 * 2. Compile: csc StowMobileRacking.cs
 * 3. Run: StowMobileRacking.exe
 * 
 * Requirements:
 * - .NET Framework 4.0 or higher
 * - Network access to Mobile Racking system (1.1.1.2:2000)
 * - Mobile Racking software active on PLC
 * 
 * Expected Behavior:
 * - Connects to Mobile Racking system
 * - Sends status request (0, 2)
 * - Sends open aisle command (1, 1)
 * - Displays responses if Mobile Racking software is active
 * - Shows connection info and any errors
 */
