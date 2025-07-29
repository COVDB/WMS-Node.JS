"""
Demo script for WMS TCP-IP communication
Test script to demonstrate functionality
"""

import time
import struct
from tcp_client import TCPClient
from wms_protocol import WMSCommands
from utils.data_parser import validate_status_data, format_timestamp
from utils.logger import wms_logger

def demo_tcp_communication():
    """Demonstrate TCP-IP communication"""
    print("=== WMS Mobile Racking TCP-IP Demo ===\n")
    
    # Configuration
    host = "127.0.0.1"  # For local test
    port = 2000
    
    print(f"Connecting to {host}:{port}...")
    
    # Create connection
    with TCPClient(host, port) as client:
        if not client.connect():
            print("❌ Cannot establish connection")
            print("💡 Tip: Start a test server first or adjust the IP address")
            return
        
        print("✅ Connection successful!\n")
        
        # Test commands
        test_commands = [
            ("Status Request", WMSCommands.STATUS_REQUEST),
            ("Start Operation", WMSCommands.START_OPERATION),
            ("Set Automatic Mode", WMSCommands.SET_AUTOMATIC_MODE),
        ]
        
        for name, command in test_commands:
            print(f"📤 Sending: {name} (Command: {command})")
            
            response = client.send_command(command)
            if response:
                print(f"📥 Response received: {len(response)} bytes")
                print(f"   Hex: {response.hex()}")
                
                # Parse as status response
                if command == WMSCommands.STATUS_REQUEST:
                    status = client.parse_status_response(response)
                    if status:
                        print("📊 Parsed status:")
                        validation = validate_status_data(status)
                        
                        # Show important parameters
                        important_params = [
                            'tcp_ip_connection', 'power_on', 
                            'automatic_mode_on', 'manual_mode_on',
                            'mobile_quantity'
                        ]
                        
                        for param in important_params:
                            if param in status:
                                print(f"   {param}: {status[param]}")
                        
                        # Show warnings/errors
                        if validation['errors']:
                            print("   🚨 Errors:")
                            for error in validation['errors']:
                                print(f"     - {error}")
                        
                        if validation['warnings']:
                            print("   ⚠️  Warnings:")
                            for warning in validation['warnings']:
                                print(f"     - {warning}")
            else:
                print("❌ No response received")
            
            print()
            time.sleep(1)  # Short pause between commands

def create_test_server():
    """Create a simple test server for demo purposes"""
    import socket
    import threading
    
    def handle_client(conn, addr):
        """Handle client connection"""
        print(f"Test server: Client connected from {addr}")
        
        try:
            while True:
                # Receive 2-byte command
                data = conn.recv(2)
                if not data:
                    break
                
                command = struct.unpack('<H', data)[0]
                print(f"Test server: Command received: {command}")
                
                # Send mock 20-byte response
                mock_response = bytearray(20)
                
                # Set some test values
                mock_response[0:2] = struct.pack('<H', command)  # Echo command
                mock_response[2] = 1  # Command start operation = True
                mock_response[4] = 2  # Version major
                mock_response[5] = 5  # Version minor
                mock_response[8] = 1  # TCP connection = True
                mock_response[9] = 1  # Auto mode = True
                mock_response[14] = 1  # Power = True
                mock_response[15] = 4  # Mobile quantity = 4
                
                conn.send(bytes(mock_response))
                print(f"Test server: Response sent: {len(mock_response)} bytes")
                
        except Exception as e:
            print(f"Test server error: {e}")
        finally:
            conn.close()
            print(f"Test server: Client {addr} disconnected")
    
    def start_server():
        """Start the test server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('127.0.0.1', 2000))
            server_socket.listen(1)
            print("🖥️  Test server started on 127.0.0.1:2000")
            print("   Waiting for connections...\n")
            
            while True:
                conn, addr = server_socket.accept()
                client_thread = threading.Thread(
                    target=handle_client, 
                    args=(conn, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n🛑 Test server stopped")
        except Exception as e:
            print(f"Test server error: {e}")
        finally:
            server_socket.close()
    
    # Start server in thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    return server_thread

if __name__ == "__main__":
    print("WMS Mobile Racking Demo\n")
    print("Choose an option:")
    print("1. Start test server and demo client")
    print("2. Demo client only (connect to external server)")
    print("3. Test server only")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 Starting test server...")
        server_thread = create_test_server()
        time.sleep(2)  # Give server time to start
        
        print("🚀 Starting demo client...")
        demo_tcp_communication()
        
    elif choice == "2":
        host = input("IP address (Enter for 1.1.1.2): ").strip() or "1.1.1.2"
        demo_tcp_communication()
        
    elif choice == "3":
        print("\n🖥️  Starting test server only...")
        server_thread = create_test_server()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Test server stopped")
    
    else:
        print("Invalid choice")
