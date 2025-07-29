#!/usr/bin/env python3
"""
Direct TCP test script for WMS Mobile Racking system
Tests the connection and command protocol directly
"""

import socket
import struct
import time

def test_tcp_connection():
    """Test direct TCP connection to PLC"""
    host = "1.1.1.2"
    port = 2000
    
    print(f"🔌 Testing TCP connection to {host}:{port}")
    print("=" * 50)
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        
        print("📡 Connecting...")
        start_time = time.time()
        sock.connect((host, port))
        connect_time = time.time() - start_time
        print(f"✅ Connected successfully in {connect_time:.2f}s")
        
        # Send status command (0) - little endian format
        command = 0
        print(f"\n📤 Sending status command: {command}")
        
        # Pack as little endian unsigned short (2 bytes)
        command_bytes = struct.pack('<H', command)
        print(f"📦 Command bytes: {command_bytes.hex().upper()} (hex)")
        print(f"📦 Command bytes: {[hex(b) for b in command_bytes]} (array)")
        
        # Send command
        bytes_sent = sock.send(command_bytes)
        print(f"📤 Sent {bytes_sent} bytes")
        
        # Wait for response
        print("\n⏳ Waiting for response...")
        start_time = time.time()
        
        try:
            response = sock.recv(1024)
            response_time = time.time() - start_time
            
            if response:
                print(f"📥 Response received in {response_time:.2f}s")
                print(f"📊 Response length: {len(response)} bytes")
                print(f"📊 Raw bytes (hex): {response.hex().upper()}")
                print(f"📊 Raw bytes (array): {[hex(b) for b in response]}")
                
                # Try to parse as expected 20-byte response
                if len(response) >= 20:
                    print(f"\n🔍 Parsing 20-byte response:")
                    try:
                        # Parse first few fields as example
                        tcp_conn = bool(response[0])
                        power_on = bool(response[1])
                        auto_mode = bool(response[2])
                        mobile_qty = response[3]
                        
                        print(f"   TCP Connection: {tcp_conn}")
                        print(f"   Power On: {power_on}")
                        print(f"   Auto Mode: {auto_mode}")
                        print(f"   Mobile Quantity: {mobile_qty}")
                        
                    except Exception as parse_err:
                        print(f"❌ Parse error: {parse_err}")
                else:
                    print(f"⚠️ Response too short (expected 20 bytes, got {len(response)})")
                
                return True
            else:
                print("❌ No response received")
                return False
                
        except socket.timeout:
            print("⏰ Response timeout (10 seconds)")
            return False
            
    except ConnectionRefusedError:
        print("❌ Connection refused - PLC may not be listening on this port")
        return False
    except socket.timeout:
        print("⏰ Connection timeout - PLC may be unreachable")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        try:
            sock.close()
            print("\n🔌 Connection closed")
        except:
            pass

def test_multiple_ports():
    """Test multiple ports to find the active one"""
    host = "1.1.1.2"
    ports = [2000, 2001, 2002]
    
    print(f"\n🔍 Testing multiple ports on {host}")
    print("=" * 50)
    
    for port in ports:
        print(f"\n🔌 Testing port {port}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port}: OPEN")
            else:
                print(f"❌ Port {port}: CLOSED")
        except Exception as e:
            print(f"❌ Port {port}: ERROR - {e}")

if __name__ == "__main__":
    print("🏭 Stow WMS Mobile Racking - Direct TCP Test")
    print("=" * 60)
    
    # Test connection first
    success = test_tcp_connection()
    
    if not success:
        # If failed, test other ports
        test_multiple_ports()
    
    print("\n" + "=" * 60)
    print("Test completed!")
