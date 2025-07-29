"""
Multi-Language Protocol Generators for WMS Mobile Racking Communication
Generates TCP-IP communication code in various programming languages
"""

import json
from typing import Dict, Any, List
from wms_protocol import WMSCommands

class ProtocolGenerator:
    """Base class for protocol code generators"""
    
    def __init__(self):
        self.language = "base"
        self.file_extension = ".txt"
    
    def generate_connection_code(self, host: str, port: int) -> str:
        """Generate connection establishment code"""
        raise NotImplementedError
    
    def generate_command_code(self, command: int, description: str = "") -> str:
        """Generate command sending code"""
        raise NotImplementedError
    
    def generate_status_request_code(self) -> str:
        """Generate status request code"""
        return self.generate_command_code(WMSCommands.STATUS_REQUEST, "Status Request")
    
    def generate_parsing_code(self) -> str:
        """Generate response parsing code"""
        raise NotImplementedError
    
    def generate_complete_example(self, host: str, port: int) -> str:
        """Generate complete working example"""
        raise NotImplementedError

class NodeJSGenerator(ProtocolGenerator):
    """Node.js TCP-IP communication code generator"""
    
    def __init__(self):
        super().__init__()
        self.language = "Node.js"
        self.file_extension = ".js"
    
    def generate_connection_code(self, host: str, port: int) -> str:
        return f"""const net = require('net');

// Create TCP client
const client = new net.Socket();

// Connection setup
client.connect({port}, '{host}', () => {{
    console.log('Connected to WMS Mobile Racking at {host}:{port}');
}});

// Error handling
client.on('error', (err) => {{
    console.error('Connection error:', err.message);
}});

client.on('close', () => {{
    console.log('Connection closed');
}});"""

    def generate_command_code(self, command: int, description: str = "") -> str:
        comment = f"// {description}" if description else ""
        return f"""{comment}
const command = {command};
const buffer = Buffer.allocUnsafe(2);
buffer.writeUInt16LE(command, 0);

client.write(buffer, (err) => {{
    if (err) {{
        console.error('Error sending command:', err);
    }} else {{
        console.log('Command {command} sent successfully');
    }}
}});"""

    def generate_parsing_code(self) -> str:
        return """// Response parsing
client.on('data', (data) => {
    console.log('Received data:', data.length, 'bytes');
    console.log('Hex:', data.toString('hex'));
    
    if (data.length === 20) {
        // Parse 20-byte status response
        const status = {
            tcp_ip_connection: data.readUInt16LE(0) === 1,
            power_on: data.readUInt16LE(2) === 1,
            automatic_mode_on: data.readUInt16LE(4) === 1,
            manual_mode_on: data.readUInt16LE(6) === 1,
            emergency_stop: data.readUInt16LE(8) === 1,
            mobile_quantity: data.readUInt16LE(10),
            position_1: data.readUInt16LE(12) / 100.0, // Convert to meters
            position_2: data.readUInt16LE(14) / 100.0, // Convert to meters
            lighting_on: data.readUInt16LE(16) === 1,
            timestamp: new Date()
        };
        
        console.log('Parsed status:', JSON.stringify(status, null, 2));
        return status;
    }
    
    return null;
});"""

    def generate_complete_example(self, host: str, port: int) -> str:
        return f"""const net = require('net');

class WMSClient {{
    constructor(host, port) {{
        this.host = host;
        this.port = port;
        this.client = new net.Socket();
        this.connected = false;
        this.setupEventHandlers();
    }}
    
    setupEventHandlers() {{
        this.client.on('connect', () => {{
            console.log(`Connected to WMS at ${{this.host}}:${{this.port}}`);
            this.connected = true;
        }});
        
        this.client.on('error', (err) => {{
            console.error('Connection error:', err.message);
            this.connected = false;
        }});
        
        this.client.on('close', () => {{
            console.log('Connection closed');
            this.connected = false;
        }});
        
        this.client.on('data', (data) => {{
            this.handleResponse(data);
        }});
    }}
    
    connect() {{
        return new Promise((resolve, reject) => {{
            this.client.connect(this.port, this.host, () => {{
                resolve(true);
            }});
            
            this.client.on('error', (err) => {{
                reject(err);
            }});
        }});
    }}
    
    sendCommand(command) {{
        if (!this.connected) {{
            throw new Error('Not connected');
        }}
        
        const buffer = Buffer.allocUnsafe(2);
        buffer.writeUInt16LE(command, 0);
        
        return new Promise((resolve, reject) => {{
            this.client.write(buffer, (err) => {{
                if (err) {{
                    reject(err);
                }} else {{
                    console.log(`Command ${{command}} sent`);
                    resolve(true);
                }}
            }});
        }});
    }}
    
    handleResponse(data) {{
        console.log('Response received:', data.length, 'bytes');
        
        if (data.length === 20) {{
            const status = this.parseStatus(data);
            console.log('Status:', JSON.stringify(status, null, 2));
            return status;
        }}
    }}
    
    parseStatus(data) {{
        return {{
            tcp_ip_connection: data.readUInt16LE(0) === 1,
            power_on: data.readUInt16LE(2) === 1,
            automatic_mode_on: data.readUInt16LE(4) === 1,
            manual_mode_on: data.readUInt16LE(6) === 1,
            emergency_stop: data.readUInt16LE(8) === 1,
            mobile_quantity: data.readUInt16LE(10),
            position_1: data.readUInt16LE(12) / 100.0,
            position_2: data.readUInt16LE(14) / 100.0,
            lighting_on: data.readUInt16LE(16) === 1,
            timestamp: new Date()
        }};
    }}
    
    disconnect() {{
        if (this.connected) {{
            this.client.end();
        }}
    }}
}}

// Usage example
async function main() {{
    const wms = new WMSClient('{host}', {port});
    
    try {{
        await wms.connect();
        
        // Send status request
        await wms.sendCommand(0);
        
        // Send other commands
        // await wms.sendCommand(1); // Start operation
        // await wms.sendCommand(3); // Set automatic mode
        
    }} catch (error) {{
        console.error('Error:', error.message);
    }}
}}

// Run the example
main();"""

class CSharpGenerator(ProtocolGenerator):
    """C# TCP-IP communication code generator (based on Stow example)"""
    
    def __init__(self):
        super().__init__()
        self.language = "C#"
        self.file_extension = ".cs"
    
    def generate_connection_code(self, host: str, port: int) -> str:
        return f"""using System;
using System.Net.Sockets;
using System.Threading.Tasks;

// TCP client setup (based on Stow Mobile Racking example)
TcpClient client = new TcpClient();

try
{{
    // Typical response times are below 30 ms, here we wait for a maximum of 5000ms/packet
    client.ReceiveTimeout = 5000;
    
    await client.ConnectAsync("{host}", {port});
    Console.WriteLine("Connected to Mobile Racking at {host}:{port}");
    
    NetworkStream stream = client.GetStream();
    var connection = new StowMobileComm();
    
    // Initialize connection for the installer
    // In his first attempt he asks for the status of the installation
    var response = connection.Transmit(0, true, true);
    Console.WriteLine($"Initial response: {{response}}");
}}
catch (Exception ex)
{{
    Console.WriteLine($"Connection error: {{ex.Message}}");
}}"""

    def generate_command_code(self, command: int, description: str = "") -> str:
        comment = f"// {description}" if description else ""
        return f"""{comment}
// Send command using Stow protocol format
// Command bytes according to PDF specification
byte[] commandBytes = new byte[4];

if ({command} == 0) {{
    // Status request: (0, 2)
    BitConverter.GetBytes((ushort)0).CopyTo(commandBytes, 0);
    BitConverter.GetBytes((ushort)2).CopyTo(commandBytes, 2);
}} else if ({command} >= 1 && {command} <= 19) {{
    // Open aisle: (aisle_number, 1)
    BitConverter.GetBytes((ushort){command}).CopyTo(commandBytes, 0);
    BitConverter.GetBytes((ushort)1).CopyTo(commandBytes, 2);
}}

await stream.WriteAsync(commandBytes, 0, commandBytes.Length);
Console.WriteLine($"Command {{string.Join(" ", commandBytes.Select(b => b.ToString("X2")))}} sent");"""

    def generate_parsing_code(self) -> str:
        return """// Response parsing with MobileResponse class (based on Stow example)
public class MobileResponse
{
    public const int responseLength = 20;
    
    public bool can_open { get; set; } = false;
    public bool ready_to_operate { get; set; } = false;
    public bool power_on { get; set; } = false;
    public bool automatic_mode_on { get; set; } = false;
    // Add other properties as needed
    
    public MobileResponse(byte[] data)
    {
        if (data.Length != responseLength)
            throw new IndexOutOfRangeException("MobileResponse - incorrect length data");
            
        // The incoming data contains one 32-bit word per status field, not bytes
        if (!BitConverter.IsLittleEndian)
        {
            // This code runs on a big endian machine, reverse the incoming bytes
            for (int i = 0; i < data.Length; i += 2)
            {
                Array.Reverse(data, i, 2);
            }
        }
        
        // Parse response data
        can_open = BitConverter.ToUInt16(data, 0) == 1;
        ready_to_operate = BitConverter.ToUInt16(data, 2) == 1;
        power_on = BitConverter.ToUInt16(data, 4) == 1;
        automatic_mode_on = BitConverter.ToUInt16(data, 6) == 1;
    }
}

// Usage in response handling
byte[] responseBuffer = new byte[20];
int bytesRead = await stream.ReadAsync(responseBuffer, 0, responseBuffer.Length);

if (bytesRead == 20)
{
    var response = new MobileResponse(responseBuffer);
    Console.WriteLine($"Can Open: {response.can_open}");
    Console.WriteLine($"Power On: {response.power_on}");
    Console.WriteLine($"Auto Mode: {response.automatic_mode_on}");
}"""

    def generate_complete_example(self, host: str, port: int) -> str:
        return f"""using System;
using System.Net.Sockets;
using System.Threading.Tasks;
using System.Linq;

namespace MobileCommTest
{{
    class Program
    {{
        static void Main(string[] args)
        {{
            // In this example, the programmer asks for the status of the installation in his first request
            // In his second request, he opens aisle number "1"
            
            var client = new TcpClient();
            
            try
            {{
                client.ReceiveTimeout = 5000; // 5000ms timeout
                client.Connect("{host}", {port});
                
                Console.WriteLine("Connected to Mobile Racking system");
                
                var stream = client.GetStream();
                
                // Test status request - send (0, 2) per PDF spec
                Console.WriteLine("\\nSending status request...");
                byte[] statusCmd = new byte[4];
                BitConverter.GetBytes((ushort)0).CopyTo(statusCmd, 0);  // byte1 = 0
                BitConverter.GetBytes((ushort)2).CopyTo(statusCmd, 2);  // byte2 = 2
                
                stream.Write(statusCmd, 0, statusCmd.Length);
                Console.WriteLine($"Status command sent: {{string.Join(" ", statusCmd.Select(b => b.ToString("X2")))}}");
                
                // Read response
                var response = GetResponse(stream);
                if (response != null)
                {{
                    Console.WriteLine($"Status response received: {{response}}");
                }}
                
                // Test aisle 1 open command - send (1, 1) per PDF spec
                Console.WriteLine("\\nSending open aisle 1 command...");
                byte[] aisleCmd = new byte[4];
                BitConverter.GetBytes((ushort)1).CopyTo(aisleCmd, 0);   // byte1 = 1 (aisle number)
                BitConverter.GetBytes((ushort)1).CopyTo(aisleCmd, 2);   // byte2 = 1 (open command)
                
                stream.Write(aisleCmd, 0, aisleCmd.Length);
                Console.WriteLine($"Aisle command sent: {{string.Join(" ", aisleCmd.Select(b => b.ToString("X2")))}}");
                
                // Read response
                response = GetResponse(stream);
                if (response != null)
                {{
                    Console.WriteLine($"Aisle response received: {{response}}");
                }}
                
            }}
            catch (Exception ex)
            {{
                Console.WriteLine($"Error: {{ex.Message}}");
            }}
            finally
            {{
                client?.Close();
            }}
            
            Console.WriteLine("\\nPress any key to exit...");
            Console.ReadKey();
        }}
        
        static MobileResponse GetResponse(NetworkStream stream)
        {{
            try
            {{
                byte[] buffer = new byte[MobileResponse.responseLength];
                int bytesRead = stream.Read(buffer, 0, buffer.Length);
                
                if (bytesRead == MobileResponse.responseLength)
                {{
                    return new MobileResponse(buffer);
                }}
                else
                {{
                    Console.WriteLine($"Expected {{MobileResponse.responseLength}} bytes, got {{bytesRead}}");
                    return null;
                }}
            }}
            catch (Exception ex)
            {{
                Console.WriteLine($"Error reading response: {{ex.Message}}");
                return null;
            }}
        }}
    }}
    
    public class MobileResponse
    {{
        public const int responseLength = 20;
        
        public bool can_open {{ get; set; }} = false;
        public bool ready_to_operate {{ get; set; }} = false;
        public bool manual_mode {{ get; set; }} = false;
        public bool power_on {{ get; set; }} = false;
        public bool automatic_mode_on {{ get; set; }} = false;
        public bool night_mode {{ get; set; }} = false;
        public bool moving {{ get; set; }} = false;
        public bool lighting_on {{ get; set; }} = false;
        public ushort mobile_quantity {{ get; set; }} = 0;
        public ushort position_1 {{ get; set; }} = 0;
        public ushort position_2 {{ get; set; }} = 0;
        
        public MobileResponse(byte[] data)
        {{
            if (data.Length != responseLength)
                throw new IndexOutOfRangeException("MobileResponse - incorrect length data");
                
            // The incoming data contains one 32-bit word per status field, not bytes
            if (!BitConverter.IsLittleEndian)
            {{
                // This code runs on a big endian machine, reverse the incoming bytes
                for (int i = 0; i < data.Length; i += 2)
                {{
                    Array.Reverse(data, i, 2);
                }}
            }}
            
            // Parse according to Mobile Racking protocol
            can_open = BitConverter.ToUInt16(data, 0) == 1;
            ready_to_operate = BitConverter.ToUInt16(data, 2) == 1;
            manual_mode = BitConverter.ToUInt16(data, 4) == 1;
            power_on = BitConverter.ToUInt16(data, 6) == 1;
            automatic_mode_on = BitConverter.ToUInt16(data, 8) == 1;
            night_mode = BitConverter.ToUInt16(data, 10) == 1;
            moving = BitConverter.ToUInt16(data, 12) == 1;
            lighting_on = BitConverter.ToUInt16(data, 14) == 1;
            mobile_quantity = BitConverter.ToUInt16(data, 16);
            position_1 = BitConverter.ToUInt16(data, 18);
        }}
        
        public override string ToString()
        {{
            return $"Can Open: {{can_open}}, Ready: {{ready_to_operate}}, Power: {{power_on}}, " +
                   $"Auto Mode: {{automatic_mode_on}}, Mobiles: {{mobile_quantity}}, Position 1: {{position_1}}";
        }}
    }}
}}

// To compile and run:
// csc Program.cs
// Program.exe"""

class RubyGenerator(ProtocolGenerator):
    """Ruby TCP-IP communication code generator"""
    
    def __init__(self):
        super().__init__()
        self.language = "Ruby"
        self.file_extension = ".rb"
    
    def generate_connection_code(self, host: str, port: int) -> str:
        return f"""require 'socket'

# Create TCP connection
begin
  socket = TCPSocket.new('{host}', {port})
  puts "Connected to WMS Mobile Racking at {host}:{port}"
rescue => e
  puts "Connection error: #{{e.message}}"
end"""

    def generate_command_code(self, command: int, description: str = "") -> str:
        comment = f"# {description}" if description else ""
        return f"""{comment}
command = {command}
command_bytes = [command].pack('S<')  # Little-endian 16-bit

socket.write(command_bytes)
puts "Command #{{command}} sent successfully" """

    def generate_parsing_code(self) -> str:
        return """# Response parsing
response = socket.read(20)

if response && response.length == 20
  # Parse 20-byte status response
  values = response.unpack('S<*')  # Little-endian 16-bit values
  
  status = {
    tcp_ip_connection: values[0] == 1,
    power_on: values[1] == 1,
    automatic_mode_on: values[2] == 1,
    manual_mode_on: values[3] == 1,
    emergency_stop: values[4] == 1,
    mobile_quantity: values[5],
    position_1: values[6] / 100.0,
    position_2: values[7] / 100.0,
    lighting_on: values[8] == 1,
    timestamp: Time.now
  }
  
  puts "Status: #{status.to_s}"
end"""

    def generate_complete_example(self, host: str, port: int) -> str:
        return f"""require 'socket'
require 'json'

class WMSClient
  def initialize(host, port)
    @host = host
    @port = port
    @socket = nil
  end
  
  def connect
    begin
      @socket = TCPSocket.new(@host, @port)
      puts "Connected to WMS at #{{@host}}:#{{@port}}"
      true
    rescue => e
      puts "Connection error: #{{e.message}}"
      false
    end
  end
  
  def send_command(command)
    return false unless @socket
    
    begin
      command_bytes = [command].pack('S<')
      @socket.write(command_bytes)
      puts "Command #{{command}} sent"
      true
    rescue => e
      puts "Error sending command: #{{e.message}}"
      false
    end
  end
  
  def read_status
    return nil unless @socket
    
    begin
      response = @socket.read(20)
      
      if response && response.length == 20
        values = response.unpack('S<*')
        
        status = {{
          tcp_ip_connection: values[0] == 1,
          power_on: values[1] == 1,
          automatic_mode_on: values[2] == 1,
          manual_mode_on: values[3] == 1,
          emergency_stop: values[4] == 1,
          mobile_quantity: values[5],
          position_1: values[6] / 100.0,
          position_2: values[7] / 100.0,
          lighting_on: values[8] == 1,
          timestamp: Time.now
        }}
        
        puts "Status: #{{status}}"
        status
      end
    rescue => e
      puts "Error reading status: #{{e.message}}"
      nil
    end
  end
  
  def disconnect
    @socket&.close
    puts "Disconnected"
  end
end

# Usage example
wms = WMSClient.new('{host}', {port})

if wms.connect
  # Send status request
  wms.send_command(0)
  
  # Read response
  wms.read_status
  
  # Send other commands
  # wms.send_command(1)  # Start operation
  # wms.send_command(3)  # Set automatic mode
  
  wms.disconnect
end"""

class JavaScriptGenerator(ProtocolGenerator):
    """JavaScript (Browser) WebSocket proxy code generator"""
    
    def __init__(self):
        super().__init__()
        self.language = "JavaScript"
        self.file_extension = ".js"
    
    def generate_connection_code(self, host: str, port: int) -> str:
        return f"""// Note: Direct TCP from browser requires WebSocket proxy
// This example assumes a WebSocket-to-TCP proxy server

const ws = new WebSocket('ws://localhost:8080/wms-proxy');

ws.onopen = function(event) {{
    console.log('Connected to WMS proxy');
    
    // Send connection request to {host}:{port}
    ws.send(JSON.stringify({{
        action: 'connect',
        host: '{host}',
        port: {port}
    }}));
}};

ws.onerror = function(error) {{
    console.error('WebSocket error:', error);
}};

ws.onclose = function(event) {{
    console.log('Connection closed');
}};"""

    def generate_command_code(self, command: int, description: str = "") -> str:
        comment = f"// {description}" if description else ""
        return f"""{comment}
const command = {command};

// Send command via WebSocket proxy
ws.send(JSON.stringify({{
    action: 'send_command',
    command: command
}}));

console.log(`Command ${{command}} sent via proxy`);"""

    def generate_parsing_code(self) -> str:
        return """// Response handling
ws.onmessage = function(event) {
    try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'response' && message.data) {
            const data = new Uint8Array(message.data);
            
            if (data.length === 20) {
                // Parse 20-byte status response
                const view = new DataView(data.buffer);
                
                const status = {
                    tcp_ip_connection: view.getUint16(0, true) === 1,
                    power_on: view.getUint16(2, true) === 1,
                    automatic_mode_on: view.getUint16(4, true) === 1,
                    manual_mode_on: view.getUint16(6, true) === 1,
                    emergency_stop: view.getUint16(8, true) === 1,
                    mobile_quantity: view.getUint16(10, true),
                    position_1: view.getUint16(12, true) / 100.0,
                    position_2: view.getUint16(14, true) / 100.0,
                    lighting_on: view.getUint16(16, true) === 1,
                    timestamp: new Date()
                };
                
                console.log('Status:', JSON.stringify(status, null, 2));
                return status;
            }
        }
    } catch (error) {
        console.error('Error parsing message:', error);
    }
};"""

    def generate_complete_example(self, host: str, port: int) -> str:
        return f"""// WMS Client for Browser (requires WebSocket proxy)
class WMSWebClient {{
    constructor(proxyUrl = 'ws://localhost:8080/wms-proxy') {{
        this.proxyUrl = proxyUrl;
        this.ws = null;
        this.connected = false;
        this.onStatusCallback = null;
    }}
    
    connect(host = '{host}', port = {port}) {{
        return new Promise((resolve, reject) => {{
            this.ws = new WebSocket(this.proxyUrl);
            
            this.ws.onopen = () => {{
                console.log('Connected to proxy');
                
                // Request connection to WMS
                this.ws.send(JSON.stringify({{
                    action: 'connect',
                    host: host,
                    port: port
                }}));
            }};
            
            this.ws.onmessage = (event) => {{
                this.handleMessage(event.data, resolve, reject);
            }};
            
            this.ws.onerror = (error) => {{
                console.error('WebSocket error:', error);
                reject(error);
            }};
            
            this.ws.onclose = () => {{
                console.log('Connection closed');
                this.connected = false;
            }};
        }});
    }}
    
    handleMessage(data, resolve, reject) {{
        try {{
            const message = JSON.parse(data);
            
            switch (message.type) {{
                case 'connected':
                    console.log('Connected to WMS');
                    this.connected = true;
                    if (resolve) resolve(true);
                    break;
                    
                case 'error':
                    console.error('WMS error:', message.error);
                    if (reject) reject(new Error(message.error));
                    break;
                    
                case 'response':
                    this.parseResponse(message.data);
                    break;
            }}
        }} catch (error) {{
            console.error('Error parsing message:', error);
        }}
    }}
    
    sendCommand(command) {{
        if (!this.connected) {{
            throw new Error('Not connected');
        }}
        
        this.ws.send(JSON.stringify({{
            action: 'send_command',
            command: command
        }}));
        
        console.log(`Command ${{command}} sent`);
    }}
    
    parseResponse(data) {{
        const bytes = new Uint8Array(data);
        
        if (bytes.length === 20) {{
            const view = new DataView(bytes.buffer);
            
            const status = {{
                tcp_ip_connection: view.getUint16(0, true) === 1,
                power_on: view.getUint16(2, true) === 1,
                automatic_mode_on: view.getUint16(4, true) === 1,
                manual_mode_on: view.getUint16(6, true) === 1,
                emergency_stop: view.getUint16(8, true) === 1,
                mobile_quantity: view.getUint16(10, true),
                position_1: view.getUint16(12, true) / 100.0,
                position_2: view.getUint16(14, true) / 100.0,
                lighting_on: view.getUint16(16, true) === 1,
                timestamp: new Date()
            }};
            
            console.log('Status:', status);
            
            if (this.onStatusCallback) {{
                this.onStatusCallback(status);
            }}
        }}
    }}
    
    setStatusCallback(callback) {{
        this.onStatusCallback = callback;
    }}
    
    disconnect() {{
        if (this.ws) {{
            this.ws.close();
        }}
    }}
}}

// Usage example
async function main() {{
    const wms = new WMSWebClient();
    
    // Set up status callback
    wms.setStatusCallback((status) => {{
        document.getElementById('status').textContent = JSON.stringify(status, null, 2);
    }});
    
    try {{
        await wms.connect();
        
        // Send status request
        wms.sendCommand(0);
        
        // Send other commands
        // wms.sendCommand(1); // Start operation
        // wms.sendCommand(3); // Set automatic mode
        
    }} catch (error) {{
        console.error('Error:', error.message);
    }}
}}

// Start when page loads
window.addEventListener('load', main);"""

class PythonGenerator(ProtocolGenerator):
    """Python TCP-IP communication code generator"""
    
    def __init__(self):
        super().__init__()
        self.language = "Python"
        self.file_extension = ".py"
    
    def generate_complete_example(self, host: str, port: int) -> str:
        return f"""import socket
import struct
import time
from datetime import datetime

class WMSClient:
    def __init__(self, host='{host}', port={port}):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
    
    def connect(self, timeout=10):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to WMS at {{self.host}}:{{self.port}}")
            return True
        except Exception as e:
            print(f"Connection error: {{e}}")
            return False
    
    def send_command(self, command):
        if not self.connected:
            raise Exception("Not connected")
        
        try:
            # Pack command as little-endian 16-bit unsigned integer
            command_bytes = struct.pack('<H', command)
            self.socket.send(command_bytes)
            print(f"Command {{command}} sent")
            return True
        except Exception as e:
            print(f"Error sending command: {{e}}")
            return False
    
    def read_status(self, timeout=5):
        if not self.connected:
            return None
        
        try:
            self.socket.settimeout(timeout)
            response = self.socket.recv(20)
            
            if len(response) == 20:
                return self.parse_status(response)
            else:
                print(f"Invalid response length: {{len(response)}}")
                return None
        except Exception as e:
            print(f"Error reading status: {{e}}")
            return None
    
    def parse_status(self, data):
        if len(data) != 20:
            return None
        
        # Unpack 20 bytes as 10 little-endian 16-bit unsigned integers
        values = struct.unpack('<10H', data)
        
        status = {{
            'tcp_ip_connection': values[0] == 1,
            'power_on': values[1] == 1,
            'automatic_mode_on': values[2] == 1,
            'manual_mode_on': values[3] == 1,
            'emergency_stop': values[4] == 1,
            'mobile_quantity': values[5],
            'position_1': values[6] / 100.0,  # Convert to meters
            'position_2': values[7] / 100.0,  # Convert to meters
            'lighting_on': values[8] == 1,
            'timestamp': datetime.now()
        }}
        
        return status
    
    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.connected = False
            print("Disconnected")

# Usage example
if __name__ == "__main__":
    wms = WMSClient()
    
    if wms.connect():
        # Send status request
        wms.send_command(0)
        
        # Read response
        status = wms.read_status()
        if status:
            print("Status:", status)
        
        # Send other commands
        # wms.send_command(1)  # Start operation
        # wms.send_command(3)  # Set automatic mode
        
        wms.disconnect()"""

# Protocol generator factory
PROTOCOL_GENERATORS = {
    "Node.js": NodeJSGenerator(),
    "C#": CSharpGenerator(),
    "Ruby": RubyGenerator(),
    "JavaScript": JavaScriptGenerator(),
    "Python": PythonGenerator()
}

def get_available_languages():
    """Get list of available programming languages"""
    return list(PROTOCOL_GENERATORS.keys())

def generate_protocol_code(language: str, code_type: str, host: str = "1.1.1.2", port: int = 2000, command: int = 0) -> str:
    """Generate protocol code for specified language and type"""
    if language not in PROTOCOL_GENERATORS:
        return f"Language '{language}' not supported"
    
    generator = PROTOCOL_GENERATORS[language]
    
    try:
        if code_type == "connection":
            return generator.generate_connection_code(host, port)
        elif code_type == "command":
            return generator.generate_command_code(command, f"Command {command}")
        elif code_type == "parsing":
            return generator.generate_parsing_code()
        elif code_type == "complete":
            return generator.generate_complete_example(host, port)
        else:
            return f"Code type '{code_type}' not supported"
    except Exception as e:
        return f"Error generating code: {e}"

def get_file_extension(language: str) -> str:
    """Get file extension for specified language"""
    if language in PROTOCOL_GENERATORS:
        return PROTOCOL_GENERATORS[language].file_extension
    return ".txt"
