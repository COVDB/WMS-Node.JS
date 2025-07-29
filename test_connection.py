"""
TCP Port Connectivity Test voor PLC
"""

import socket
import sys
import time

def test_tcp_connection(host, port, timeout=10):
    """Test TCP verbinding naar host:port"""
    print(f"Testing TCP verbinding naar {host}:{port}...")
    print(f"Timeout: {timeout} seconden")
    
    try:
        # Maak socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Probeer verbinding
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        
        sock.close()
        
        if result == 0:
            print(f"✅ Verbinding SUCCESVOL naar {host}:{port}")
            print(f"   Verbindingstijd: {(end_time - start_time)*1000:.0f}ms")
            return True
        else:
            print(f"❌ Verbinding MISLUKT naar {host}:{port}")
            print(f"   Error code: {result}")
            return False
            
    except socket.timeout:
        print(f"⏰ TIMEOUT na {timeout} seconden")
        return False
    except socket.gaierror as e:
        print(f"🌐 DNS FOUT: {e}")
        return False
    except Exception as e:
        print(f"❌ ONBEKENDE FOUT: {e}")
        return False

def test_tcp_send_receive(host, port, timeout=10):
    """Test TCP verbinding met data uitwisseling"""
    print(f"\nTesting TCP data uitwisseling naar {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        # Verbind
        sock.connect((host, port))
        print("✅ Socket verbinding succesvol")
        
        # Stuur test command (2 bytes - command 0 voor status)
        test_command = b'\x00\x00'  # Command 0 in little endian
        sock.send(test_command)
        print(f"📤 Test command verzonden: {test_command.hex()}")
        
        # Probeer response te ontvangen (20 bytes verwacht)
        response = b""
        start_time = time.time()
        
        while len(response) < 20 and (time.time() - start_time) < timeout:
            try:
                chunk = sock.recv(20 - len(response))
                if not chunk:
                    break
                response += chunk
                print(f"📥 Chunk ontvangen: {len(chunk)} bytes")
            except socket.timeout:
                break
        
        sock.close()
        
        if len(response) == 20:
            print(f"✅ Volledige response ontvangen: {len(response)} bytes")
            print(f"   Hex data: {response.hex()}")
            return True, response
        elif len(response) > 0:
            print(f"⚠️  Gedeeltelijke response: {len(response)} bytes (verwacht 20)")
            print(f"   Hex data: {response.hex()}")
            return False, response
        else:
            print("❌ Geen response ontvangen")
            return False, None
            
    except socket.timeout:
        print(f"⏰ TIMEOUT tijdens data uitwisseling")
        return False, None
    except Exception as e:
        print(f"❌ FOUT tijdens data uitwisseling: {e}")
        return False, None

if __name__ == "__main__":
    host = "1.1.1.2"
    port = 2000
    
    print("=== PLC TCP-IP Connectiviteit Test ===\n")
    
    # Test 1: Basis connectiviteit
    print("Test 1: Basis TCP connectiviteit")
    success1 = test_tcp_connection(host, port, timeout=10)
    
    if success1:
        # Test 2: Data uitwisseling
        print("\nTest 2: TCP data uitwisseling")
        success2, response = test_tcp_send_receive(host, port, timeout=10)
        
        if success2 and response:
            print("\n🎉 ALLE TESTS SUCCESVOL!")
            print("De PLC is bereikbaar en reageert op commands.")
        elif success2:
            print("\n⚠️  GEDEELTELIJK SUCCESVOL")
            print("PLC is bereikbaar maar response is onvolledig.")
        else:
            print("\n❌ DATA UITWISSELING MISLUKT")
            print("PLC accepteert verbindingen maar reageert niet op commands.")
    else:
        print("\n❌ CONNECTIVITEIT MISLUKT")
        print("Mogelijke oorzaken:")
        print("- PLC is uit of niet bereikbaar")
        print("- Poort 2000 is niet open op de PLC")
        print("- Firewall blokkeert de verbinding")
        print("- VPN configuratie probleem")
    
    print(f"\nTest voltooid voor {host}:{port}")
