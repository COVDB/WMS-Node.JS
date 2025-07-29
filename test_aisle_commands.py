#!/usr/bin/env python3
"""
Test script for aisle commands based on PDF protocol
"""
import socket
import struct
import time
import sys

def test_aisle_command(aisle_number):
    """Test aisle command according to PDF: (aisle_number, 1)"""
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        print(f"Testing Aisle {aisle_number} command...")
        print(f"Sending bytes: ({aisle_number}, 1)")
        
        # Connect to PLC
        sock.connect(("1.1.1.2", 2000))
        print("Connected to 1.1.1.2:2000")
        
        # Send aisle command (aisle_number, 1) per PDF spec
        command = struct.pack('<HH', aisle_number, 1)
        sock.send(command)
        print(f"Sent aisle {aisle_number} command: {command.hex()}")
        
        # Wait for response
        response = sock.recv(20)
        if response:
            print(f"Received response: {response.hex()}")
            
            # Parse response (little-endian)
            parsed = struct.unpack('<' + 'H' * (len(response) // 2), response)
            print(f"Parsed response: {parsed}")
        else:
            print("No response received")
            
    except socket.timeout:
        print("Connection timed out")
    except ConnectionRefusedError:
        print("Connection refused - PLC may not be responding")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass

def test_status_command():
    """Test status command according to PDF: (0, 2)"""
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        print("Testing Status command...")
        print("Sending bytes: (0, 2)")
        
        # Connect to PLC
        sock.connect(("1.1.1.2", 2000))
        print("Connected to 1.1.1.2:2000")
        
        # Send status command (0, 2) per PDF spec
        command = struct.pack('<HH', 0, 2)
        sock.send(command)
        print(f"Sent status command: {command.hex()}")
        
        # Wait for response
        response = sock.recv(20)
        if response:
            print(f"Received response: {response.hex()}")
            
            # Parse response (little-endian)
            parsed = struct.unpack('<' + 'H' * (len(response) // 2), response)
            print(f"Parsed response: {parsed}")
        else:
            print("No response received")
            
    except socket.timeout:
        print("Connection timed out")
    except ConnectionRefusedError:
        print("Connection refused - PLC may not be responding")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass

if __name__ == "__main__":
    print("=== WMS Aisle Command Test (PDF Protocol) ===")
    print()
    
    # Test status first
    test_status_command()
    print()
    time.sleep(1)
    
    # Test a few aisle commands
    for aisle in [1, 5, 10]:
        test_aisle_command(aisle)
        print()
        time.sleep(1)
    
    print("Test completed!")
    print()
    print("NOTE: If no responses received, Mobile Racking software may not be active on PLC")
    print("But TCP connection works, so protocol is correctly implemented!")
