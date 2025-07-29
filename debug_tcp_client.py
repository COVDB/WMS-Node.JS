#!/usr/bin/env python3
"""
Debug version of TCP client with detailed logging
"""

import socket
import struct
import time
from typing import Optional

class DebugTCPClient:
    """Debug TCP client for Mobile Racking"""
    
    def __init__(self, host: str = "1.1.1.2", port: int = 2001):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect with detailed logging"""
        print(f"🔌 Connecting to {self.host}:{self.port}")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            
            start_time = time.time()
            self.socket.connect((self.host, self.port))
            connect_time = time.time() - start_time
            
            self.connected = True
            print(f"✅ Connected in {connect_time:.2f}s")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    def send_command_debug(self, command: int) -> Optional[bytes]:
        """Send command with detailed debugging"""
        if not self.connected or not self.socket:
            print("❌ Not connected")
            return None
            
        try:
            # Send command
            command_bytes = struct.pack('<H', command)
            print(f"📤 Sending command {command}")
            print(f"   Raw bytes: {command_bytes.hex().upper()}")
            print(f"   Length: {len(command_bytes)} bytes")
            
            bytes_sent = self.socket.send(command_bytes)
            print(f"   Sent: {bytes_sent} bytes")
            
            # Try to receive with detailed timing
            print("⏳ Waiting for response...")
            response = b""
            start_time = time.time()
            max_wait = 15.0  # 15 seconds total
            
            # Try to receive in chunks
            while len(response) < 20 and (time.time() - start_time) < max_wait:
                try:
                    self.socket.settimeout(1.0)  # 1 second per chunk
                    chunk = self.socket.recv(20 - len(response))
                    
                    if chunk:
                        response += chunk
                        elapsed = time.time() - start_time
                        print(f"   📥 Chunk: {len(chunk)} bytes (total: {len(response)}) after {elapsed:.1f}s")
                        print(f"   📥 Data: {chunk.hex().upper()}")
                    else:
                        print("   ❌ No more data (connection closed)")
                        break
                        
                except socket.timeout:
                    elapsed = time.time() - start_time
                    print(f"   ⏰ Waiting... ({elapsed:.1f}s)")
                    continue
                except Exception as e:
                    print(f"   ❌ Receive error: {e}")
                    break
            
            total_time = time.time() - start_time
            
            if response:
                print(f"✅ Response received after {total_time:.1f}s")
                print(f"   Length: {len(response)} bytes")
                print(f"   Complete data: {response.hex().upper()}")
                return response
            else:
                print(f"❌ No response after {total_time:.1f}s")
                return None
                
        except Exception as e:
            print(f"❌ Send error: {e}")
            return None
    
    def test_different_commands(self):
        """Test different command numbers"""
        test_commands = [0, 1, 2, 3, 100, 200, 65535]
        
        print("\n🧪 Testing different commands:")
        print("=" * 50)
        
        for cmd in test_commands:
            print(f"\n🔍 Testing command {cmd}:")
            response = self.send_command_debug(cmd)
            if response:
                print(f"✅ Command {cmd} got response!")
                break
            else:
                print(f"❌ Command {cmd} no response")
                time.sleep(1)  # Small delay between tests
    
    def disconnect(self):
        """Disconnect"""
        if self.socket:
            try:
                self.socket.close()
                print("🔌 Disconnected")
            except:
                pass
            finally:
                self.socket = None
                self.connected = False

def main():
    print("🔬 Debug TCP Client for WMS Mobile Racking")
    print("=" * 60)
    
    # Test both ports
    for port in [2001, 2000]:
        print(f"\n🔌 Testing port {port}")
        print("-" * 30)
        
        client = DebugTCPClient("1.1.1.2", port)
        
        if client.connect():
            # Test status command (0)
            print("\n📊 Testing status command (0):")
            response = client.send_command_debug(0)
            
            if not response:
                # If no response, try different commands
                client.test_different_commands()
            
            client.disconnect()
        else:
            print(f"❌ Could not connect to port {port}")
        
        print()

if __name__ == "__main__":
    main()
