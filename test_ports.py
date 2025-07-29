#!/usr/bin/env python3
"""
Test both ports 2000 and 2001 to see which one responds
"""

import socket
import struct
import time

def test_port(host, port):
    """Test specific port"""
    print(f"\n🔌 Testing {host}:{port}")
    print("-" * 40)
    
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Connect
        start_time = time.time()
        sock.connect((host, port))
        connect_time = time.time() - start_time
        print(f"✅ Connected in {connect_time:.2f}s")
        
        # Send status command (0)
        command = 0
        command_bytes = struct.pack('<H', command)
        print(f"📤 Sending command {command}: {command_bytes.hex().upper()}")
        
        bytes_sent = sock.send(command_bytes)
        print(f"📤 Sent {bytes_sent} bytes")
        
        # Try to receive response
        print("⏳ Waiting for response (5s timeout)...")
        start_time = time.time()
        
        try:
            response = sock.recv(1024)
            response_time = time.time() - start_time
            
            if response:
                print(f"📥 SUCCESS! Response in {response_time:.2f}s")
                print(f"📊 Length: {len(response)} bytes")
                print(f"📊 Hex: {response.hex().upper()}")
                
                if len(response) >= 4:
                    # Try to parse first few bytes
                    try:
                        val1 = response[0]
                        val2 = response[1]
                        val3 = response[2]
                        val4 = response[3]
                        print(f"📊 First 4 bytes: {val1}, {val2}, {val3}, {val4}")
                    except:
                        pass
                
                return True
            else:
                print("❌ Empty response")
                return False
                
        except socket.timeout:
            print("⏰ No response (timeout)")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass

def main():
    host = "1.1.1.2"
    
    print("🏭 Stow WMS - Port Response Test")
    print("=" * 50)
    
    # Test port 2000
    result_2000 = test_port(host, 2000)
    
    # Test port 2001
    result_2001 = test_port(host, 2001)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Port 2000: {'✅ RESPONDS' if result_2000 else '❌ NO RESPONSE'}")
    print(f"Port 2001: {'✅ RESPONDS' if result_2001 else '❌ NO RESPONSE'}")
    
    if result_2001 and not result_2000:
        print("\n💡 SOLUTION: Use port 2001 instead of 2000!")
    elif result_2000 and not result_2001:
        print("\n💡 SOLUTION: Use port 2000 (current default)")
    elif result_2000 and result_2001:
        print("\n💡 Both ports respond - either can be used")
    else:
        print("\n❌ Neither port responds - check PLC configuration")

if __name__ == "__main__":
    main()
