#!/usr/bin/env python3
"""
Test with CORRECT protocol from PDF
Status request: first byte = 0, second byte = 2
"""

import socket
import struct
import time

def test_correct_protocol():
    """Test with the correct protocol from PDF"""
    host = "1.1.1.2"
    port = 2000  # PDF says port 2000
    
    print("🔬 Testing CORRECT protocol from PDF")
    print("=" * 50)
    print("Status request: byte 1 = 0, byte 2 = 2")
    print("Expected response: 20 bytes")
    print()
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        print(f"🔌 Connecting to {host}:{port}...")
        start_time = time.time()
        sock.connect((host, port))
        connect_time = time.time() - start_time
        print(f"✅ Connected in {connect_time:.2f}s")
        
        # CORRECT STATUS COMMAND according to PDF:
        # First byte = 0, Second byte = 2
        command_bytes = struct.pack('BB', 0, 2)  # Two separate bytes
        
        print(f"\n📤 Sending CORRECT status command:")
        print(f"   Bytes: {command_bytes.hex().upper()}")
        print(f"   Meaning: Status request (0, 2)")
        
        bytes_sent = sock.send(command_bytes)
        print(f"   Sent: {bytes_sent} bytes")
        
        # Wait for 20-byte response
        print("\n⏳ Waiting for 20-byte response...")
        start_time = time.time()
        
        response = sock.recv(20)
        response_time = time.time() - start_time
        
        if response:
            print(f"🎉 SUCCESS! Response received in {response_time:.2f}s")
            print(f"📊 Length: {len(response)} bytes (expected: 20)")
            print(f"📊 Raw hex: {response.hex().upper()}")
            
            # Parse first few bytes according to PDF structure
            if len(response) >= 20:
                print(f"\n🔍 Parsing response structure:")
                
                # Based on the WMS data structure shown in PDF
                try:
                    # First few fields from the table
                    status_req_aisle = response[0]
                    cmd_start_opening = bool(response[1])
                    cmd_request_status = bool(response[2])
                    
                    print(f"   Status Request Aisle: {status_req_aisle}")
                    print(f"   Command Start Opening: {cmd_start_opening}")
                    print(f"   Command Request Status: {cmd_request_status}")
                    
                    # More fields (continuing from table)
                    if len(response) >= 6:
                        stow_major = response[4]
                        stow_minor = response[5]
                        print(f"   Stow Version: {stow_major}.{stow_minor}")
                    
                except Exception as e:
                    print(f"   Parse error: {e}")
            
            return True
        else:
            print("❌ Empty response")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            sock.close()
            print("\n🔌 Connection closed")
        except:
            pass

def test_open_aisle_command():
    """Test opening aisle command"""
    host = "1.1.1.2"
    port = 2000
    aisle_number = 1  # Test aisle 1
    
    print(f"\n🚪 Testing OPEN AISLE command (aisle {aisle_number})")
    print("=" * 50)
    print("Open aisle: byte 1 = aisle number, byte 2 = 1")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        sock.connect((host, port))
        print(f"✅ Connected to {host}:{port}")
        
        # OPEN AISLE COMMAND according to PDF:
        # First byte = aisle number (1-19), Second byte = 1
        command_bytes = struct.pack('BB', aisle_number, 1)
        
        print(f"\n📤 Sending open aisle command:")
        print(f"   Bytes: {command_bytes.hex().upper()}")
        print(f"   Meaning: Open aisle {aisle_number}")
        
        sock.send(command_bytes)
        
        # Wait for response
        response = sock.recv(20)
        
        if response:
            print(f"✅ Open aisle response: {len(response)} bytes")
            print(f"📊 Data: {response.hex().upper()}")
            return True
        else:
            print("❌ No response to open aisle command")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    print("🏭 Stow WMS - CORRECT Protocol Test (from PDF)")
    print("=" * 60)
    
    # Test status request first
    success = test_correct_protocol()
    
    if success:
        print("\n" + "="*60)
        print("🎉 STATUS COMMAND WORKS!")
        print("The protocol documentation was the key!")
        
        # Also test open aisle command (but be careful in production!)
        response = input("\nDo you want to test OPEN AISLE command? (y/N): ")
        if response.lower() == 'y':
            test_open_aisle_command()
    else:
        print("\n❌ Status command still failed - check PLC configuration")
    
    print("\n" + "="*60)
    print("Test completed!")
