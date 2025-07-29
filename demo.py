"""
Demo script voor WMS TCP-IP communicatie
Test script om de functionaliteit te demonstreren
"""

import time
import struct
from tcp_client import TCPClient
from wms_protocol import WMSCommands
from utils.data_parser import validate_status_data, format_timestamp
from utils.logger import wms_logger

def demo_tcp_communication():
    """Demonstreer TCP-IP communicatie"""
    print("=== WMS Mobile Racking TCP-IP Demo ===\n")
    
    # Configuratie
    host = "127.0.0.1"  # Voor lokale test
    port = 2000
    
    print(f"Verbinden naar {host}:{port}...")
    
    # Maak verbinding
    with TCPClient(host, port) as client:
        if not client.connect():
            print("❌ Kan geen verbinding maken")
            print("💡 Tip: Start eerst een test server of pas het IP adres aan")
            return
        
        print("✅ Verbinding succesvol!\n")
        
        # Test commands
        test_commands = [
            ("Status Request", WMSCommands.STATUS_REQUEST),
            ("Start Operation", WMSCommands.START_OPERATION),
            ("Set Automatic Mode", WMSCommands.SET_AUTOMATIC_MODE),
        ]
        
        for name, command in test_commands:
            print(f"📤 Verzenden: {name} (Command: {command})")
            
            response = client.send_command(command)
            if response:
                print(f"📥 Response ontvangen: {len(response)} bytes")
                print(f"   Hex: {response.hex()}")
                
                # Parse als status response
                if command == WMSCommands.STATUS_REQUEST:
                    status = client.parse_status_response(response)
                    if status:
                        print("📊 Geparsde status:")
                        validation = validate_status_data(status)
                        
                        # Toon belangrijke parameters
                        important_params = [
                            'tcp_ip_connection', 'power_on', 
                            'automatic_mode_on', 'manual_mode_on',
                            'mobile_quantity'
                        ]
                        
                        for param in important_params:
                            if param in status:
                                print(f"   {param}: {status[param]}")
                        
                        # Toon warnings/errors
                        if validation['errors']:
                            print("   🚨 Errors:")
                            for error in validation['errors']:
                                print(f"     - {error}")
                        
                        if validation['warnings']:
                            print("   ⚠️  Warnings:")
                            for warning in validation['warnings']:
                                print(f"     - {warning}")
            else:
                print("❌ Geen response ontvangen")
            
            print()
            time.sleep(1)  # Korte pauze tussen commands

def create_test_server():
    """Maak een simpele test server voor demo doeleinden"""
    import socket
    import threading
    
    def handle_client(conn, addr):
        """Handle client verbinding"""
        print(f"Test server: Client verbonden vanaf {addr}")
        
        try:
            while True:
                # Ontvang 2-byte command
                data = conn.recv(2)
                if not data:
                    break
                
                command = struct.unpack('<H', data)[0]
                print(f"Test server: Command ontvangen: {command}")
                
                # Stuur mock 20-byte response
                mock_response = bytearray(20)
                
                # Zet wat test waarden
                mock_response[0:2] = struct.pack('<H', command)  # Echo command
                mock_response[2] = 1  # Command start operation = True
                mock_response[4] = 2  # Version major
                mock_response[5] = 5  # Version minor
                mock_response[8] = 1  # TCP connection = True
                mock_response[9] = 1  # Auto mode = True
                mock_response[14] = 1  # Power = True
                mock_response[15] = 4  # Mobile quantity = 4
                
                conn.send(bytes(mock_response))
                print(f"Test server: Response verzonden: {len(mock_response)} bytes")
                
        except Exception as e:
            print(f"Test server error: {e}")
        finally:
            conn.close()
            print(f"Test server: Client {addr} verbroken")
    
    def start_server():
        """Start de test server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('127.0.0.1', 2000))
            server_socket.listen(1)
            print("🖥️  Test server gestart op 127.0.0.1:2000")
            print("   Wachtend op verbindingen...\n")
            
            while True:
                conn, addr = server_socket.accept()
                client_thread = threading.Thread(
                    target=handle_client, 
                    args=(conn, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n🛑 Test server gestopt")
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
    print("Kies een optie:")
    print("1. Start test server en demo client")
    print("2. Alleen demo client (verbind naar externe server)")
    print("3. Alleen test server")
    
    choice = input("\nKeuze (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 Starten test server...")
        server_thread = create_test_server()
        time.sleep(2)  # Geef server tijd om te starten
        
        print("🚀 Starten demo client...")
        demo_tcp_communication()
        
    elif choice == "2":
        host = input("IP adres (Enter voor 1.1.1.2): ").strip() or "1.1.1.2"
        demo_tcp_communication()
        
    elif choice == "3":
        print("\n🖥️  Alleen test server starten...")
        server_thread = create_test_server()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Test server gestopt")
    
    else:
        print("Ongeldige keuze")
