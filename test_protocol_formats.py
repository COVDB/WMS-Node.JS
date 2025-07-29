#!/usr/bin/env python3
"""
Test different command formats to see what works
Based on different protocol interpretations
"""

import socket
import struct
import time

def test_command_format(host, port, command_data, description):
    """Test specific command format"""
    print(f"\n🧪 Testing: {description}")
    print(f"📦 Data: {command_data.hex().upper()} ({len(command_data)} bytes)")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        
        sock.connect((host, port))
        sock.send(command_data)
        
        # Try to get response
        try:
            response = sock.recv(1024)
            if response:
                print(f"✅ SUCCESS! Response: {response.hex().upper()}")
                return True
            else:
                print("❌ No response")
                return False
        except socket.timeout:
            print("❌ Timeout")
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
    port = 2000  # Start with 2000
    
    print("🔬 WMS Protocol Format Test")
    print("=" * 50)
    
    # Test different command formats
    test_formats = [
        # Format 1: Little endian 2-byte (current)
        (struct.pack('<H', 0), "Little Endian 2-byte: 0x0000"),
        
        # Format 2: Big endian 2-byte
        (struct.pack('>H', 0), "Big Endian 2-byte: 0x0000"),
        
        # Format 3: Single byte
        (struct.pack('B', 0), "Single Byte: 0x00"),
        
        # Format 4: 4-byte little endian
        (struct.pack('<L', 0), "Little Endian 4-byte: 0x00000000"),
        
        # Format 5: ASCII command
        (b"0\r\n", "ASCII: '0\\r\\n'"),
        
        # Format 6: ASCII command simple
        (b"0", "ASCII: '0'"),
        
        # Format 7: Different status command values
        (struct.pack('<H', 1), "Little Endian 2-byte: 0x0001"),
        (struct.pack('<H', 100), "Little Endian 2-byte: 0x0064"),
        
        # Format 8: Common industrial protocol formats
        (b"\x00\x00\x00\x00", "4 Zero bytes"),
        (b"\x01\x00", "Little Endian: 0x0001"),
    ]
    
    successful_formats = []
    
    for data, desc in test_formats:
        success = test_command_format(host, port, data, desc)
        if success:
            successful_formats.append(desc)
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    
    if successful_formats:
        print("✅ Working formats:")
        for fmt in successful_formats:
            print(f"   • {fmt}")
    else:
        print("❌ No formats worked on port 2000")
        print("\n🔄 Testing port 2001...")
        
        # Try port 2001 with first few formats
        port = 2001
        for data, desc in test_formats[:3]:
            success = test_command_format(host, port, data, desc)
            if success:
                successful_formats.append(f"Port 2001: {desc}")
    
    if not successful_formats:
        print("\n💭 Possible issues:")
        print("   • PLC Mobile Racking service not active")
        print("   • Different protocol than expected")
        print("   • Authentication/handshake required first")
        print("   • Different command for status request")

if __name__ == "__main__":
    main()
