using System;
using System.Net.Sockets;
using System.Threading.Tasks;
using System.Text.Json;

// WMS Mobile Racking Client - Generated with Streamlit App
// Language: C#
// Target: 1.1.1.2:2001
// Generated: 2025-07-29

public class WMSClient : IDisposable
{
    private TcpClient _client;
    private NetworkStream _stream;
    private readonly string _host;
    private readonly int _port;
    
    public WMSClient(string host, int port)
    {
        _host = host;
        _port = port;
        _client = new TcpClient();
    }
    
    public async Task<bool> ConnectAsync()
    {
        try
        {
            await _client.ConnectAsync(_host, _port);
            _stream = _client.GetStream();
            Console.WriteLine($"Connected to WMS at {_host}:{_port}");
            return true;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Connection error: {ex.Message}");
            return false;
        }
    }
    
    public async Task<bool> SendCommandAsync(int command)
    {
        try
        {
            byte[] commandBytes = BitConverter.GetBytes((ushort)command);
            
            if (!BitConverter.IsLittleEndian)
            {
                Array.Reverse(commandBytes);
            }
            
            await _stream.WriteAsync(commandBytes, 0, commandBytes.Length);
            Console.WriteLine($"Command {command} sent");
            return true;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error sending command: {ex.Message}");
            return false;
        }
    }
    
    public async Task<object> ReadStatusAsync()
    {
        try
        {
            byte[] responseBuffer = new byte[20];
            int bytesRead = await _stream.ReadAsync(responseBuffer, 0, responseBuffer.Length);
            
            if (bytesRead == 20)
            {
                var status = new
                {
                    TcpIpConnection = BitConverter.ToUInt16(responseBuffer, 0) == 1,
                    PowerOn = BitConverter.ToUInt16(responseBuffer, 2) == 1,
                    AutomaticModeOn = BitConverter.ToUInt16(responseBuffer, 4) == 1,
                    ManualModeOn = BitConverter.ToUInt16(responseBuffer, 6) == 1,
                    EmergencyStop = BitConverter.ToUInt16(responseBuffer, 8) == 1,
                    MobileQuantity = BitConverter.ToUInt16(responseBuffer, 10),
                    Position1 = BitConverter.ToUInt16(responseBuffer, 12) / 100.0,
                    Position2 = BitConverter.ToUInt16(responseBuffer, 14) / 100.0,
                    LightingOn = BitConverter.ToUInt16(responseBuffer, 16) == 1,
                    Timestamp = DateTime.Now
                };
                
                Console.WriteLine($"Status: {JsonSerializer.Serialize(status)}");
                return status;
            }
            
            return null;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error reading status: {ex.Message}");
            return null;
        }
    }
    
    public void Dispose()
    {
        _stream?.Dispose();
        _client?.Close();
    }
}

// Usage example
class Program
{
    static async Task Main(string[] args)
    {
        using var wms = new WMSClient("1.1.1.2", 2001);
        
        if (await wms.ConnectAsync())
        {
            // Send status request
            await wms.SendCommandAsync(0);
            
            // Read response
            await wms.ReadStatusAsync();
            
            // Send other commands
            // await wms.SendCommandAsync(1); // Start operation
            // await wms.SendCommandAsync(3); // Set automatic mode
        }
    }
}
