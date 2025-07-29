#!/usr/bin/env python3
"""
Node-RED Compatible Mobile Racking Test
Based on successful Node-RED response: [0,0,2,5,2,2,0,0,223,27,0,0,0,0,0,0,0,14,0,0]
"""
import socket
import struct
import time

def simulate_node_red_connection():
    """Test with Node-RED style connection parameters"""
    
    print("🏭 STOW MOBILE RACKING - NODE-RED COMPATIBLE TEST")
    print("=" * 60)
    print("📊 Attempting to replicate Node-RED success...")
    print()
    
    # Try different connection approaches
    connection_methods = [
        {"name": "Standard TCP", "reuse": False, "keepalive": False},
        {"name": "Reusable Socket", "reuse": True, "keepalive": False},
        {"name": "Keep-Alive", "reuse": False, "keepalive": True},
        {"name": "Full Options", "reuse": True, "keepalive": True},
    ]
    
    for method in connection_methods:
        print(f"🔄 Testing: {method['name']}")
        print("-" * 40)
        
        try:
            # Create socket with options
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            if method['reuse']:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                print("   ✅ Socket reuse enabled")
            
            if method['keepalive']:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                print("   ✅ Keep-alive enabled")
            
            # Set timeouts
            sock.settimeout(15)  # Longer timeout like Node-RED might use
            
            print("   🔌 Connecting to 1.1.1.2:2000...")
            start_time = time.time()
            sock.connect(("1.1.1.2", 2000))
            connect_time = time.time() - start_time
            print(f"   ✅ Connected in {connect_time:.3f}s")
            
            # Send status request like Node-RED would
            command = struct.pack('<HH', 0, 2)  # Status request (0, 2)
            print(f"   📤 Sending: {command.hex().upper()}")
            
            send_start = time.time()
            bytes_sent = sock.send(command)
            send_time = time.time() - send_start
            print(f"   📤 Sent {bytes_sent} bytes in {send_time:.3f}s")
            
            # Receive response with different strategies
            recv_strategies = [
                {"name": "Single recv(20)", "method": "single"},
                {"name": "recv_all helper", "method": "helper"},
                {"name": "Chunked receive", "method": "chunked"}
            ]
            
            for strategy in recv_strategies[:1]:  # Test first strategy
                print(f"   📥 Trying {strategy['name']}:")
                
                try:
                    if strategy['method'] == 'single':
                        recv_start = time.time()
                        response = sock.recv(20)
                        recv_time = time.time() - recv_start
                        
                    elif strategy['method'] == 'helper':
                        recv_start = time.time()
                        response = recv_all(sock, 20)
                        recv_time = time.time() - recv_start
                        
                    elif strategy['method'] == 'chunked':
                        recv_start = time.time()
                        response = b""
                        while len(response) < 20:
                            chunk = sock.recv(20 - len(response))
                            if not chunk:
                                break
                            response += chunk
                        recv_time = time.time() - recv_start
                    
                    if response:
                        print(f"      ✅ Received {len(response)} bytes in {recv_time:.3f}s")
                        
                        if len(response) == 20:
                            response_list = list(response)
                            print(f"      📋 Data: {response_list}")
                            
                            # Compare with Node-RED response
                            node_red_response = [0,0,2,5,2,2,0,0,223,27,0,0,0,0,0,0,0,14,0,0]
                            
                            if response_list == node_red_response:
                                print("      🎉 EXACT MATCH with Node-RED response!")
                            else:
                                print("      📊 Different response:")
                                print(f"         Expected: {node_red_response}")
                                print(f"         Received: {response_list}")
                                
                            # Parse as words
                            words = struct.unpack('<10H', response)
                            print(f"      📊 Words: {list(words)}")
                            
                            print(f"   🎯 SUCCESS with {method['name']} + {strategy['name']}!")
                            sock.close()
                            return True
                        else:
                            print(f"      ⚠️ Wrong length: {len(response)} bytes")
                    else:
                        print("      ❌ No response received")
                        
                except socket.timeout:
                    print(f"      ⏰ Timeout after {recv_time:.3f}s")
                except Exception as e:
                    print(f"      ❌ Error: {e}")
            
            sock.close()
            print()
            
        except socket.timeout:
            print("   ⏰ Connection timeout")
        except ConnectionRefusedError:
            print("   ❌ Connection refused")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("❌ No method successfully replicated Node-RED behavior")
    return False

def recv_all(sock, length):
    """Helper to receive exact number of bytes"""
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            break
        data += chunk
    return data

def check_node_red_setup():
    """Analyze what Node-RED might be doing differently"""
    
    print("🔍 NODE-RED ANALYSIS")
    print("=" * 30)
    print("Node-RED successful response: [0,0,2,5,2,2,0,0,223,27,0,0,0,0,0,0,0,14,0,0]")
    print()
    print("Possible Node-RED advantages:")
    print("1. 🔄 Connection pooling/reuse")
    print("2. ⏱️ Different timeout settings")
    print("3. 🌐 Network interface binding")
    print("4. 📦 TCP options (Nagle, etc.)")
    print("5. 🔌 Persistent connections")
    print()
    print("🚀 RECOMMENDATION:")
    print("Since Node-RED works, we should:")
    print("1. ✅ Use Node-RED for production")
    print("2. ✅ Update Streamlit app to parse the known response format")
    print("3. ✅ Focus on application logic rather than connection debugging")
    print("4. ✅ Document the working Node-RED configuration")

if __name__ == "__main__":
    success = simulate_node_red_connection()
    print()
    if not success:
        check_node_red_setup()
