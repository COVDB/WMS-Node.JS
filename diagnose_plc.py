"""
PLC Diagnostic Tool - Extended troubleshooting for TCP-IP connection
"""

import socket
import time
import struct
import subprocess
import sys
from tcp_client import TCPClient

def check_network_basics(host):
    """Check basic network connectivity"""
    print(f"=== NETWORK DIAGNOSTICS for {host} ===\n")
    
    # 1. Ping test
    print("1. Ping Test:")
    try:
        result = subprocess.run(
            ['ping', host, '-n', '4'], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Ping SUCCESSFUL")
            # Extract ping times
            lines = result.stdout.split('\n')
            for line in lines:
                if 'time=' in line or 'Average' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ Ping FAILED")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ping test error: {e}")
        return False
    
    return True

def check_port_connectivity(host, port):
    """Check TCP port connectivity with different methods"""
    print(f"\n2. TCP Port {port} Connectivity:")
    
    # Method 1: Socket connect test
    print(f"   a) Socket connect test to {host}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {port} is OPEN ({(end_time-start_time)*1000:.0f}ms)")
            return True
        else:
            print(f"   ❌ Port {port} is CLOSED (Error: {result})")
            if result == 10061:
                print("      → Connection refused - Service not running")
            elif result == 10060:
                print("      → Timeout - Host not reachable or firewall")
            return False
            
    except Exception as e:
        print(f"   ❌ Socket test error: {e}")
        return False

def test_plc_protocol(host, port):
    """Test specific PLC protocol communication"""
    print(f"\n3. PLC Protocol Test:")
    
    print(f"   Connecting to PLC at {host}:{port}...")
    
    try:
        client = TCPClient(host, port)
        
        if not client.connect():
            print("   ❌ PLC connection failed")
            return False
        
        print("   ✅ PLC connection successful!")
        
        # Test status command
        print("   Testing status command (0)...")
        response = client.send_command(0)
        
        if response:
            print(f"   ✅ Status response received: {len(response)} bytes")
            print(f"      Hex: {response.hex()}")
            
            # Parse basic status
            status = client.parse_status_response(response)
            if status:
                print("   📊 Belangrijke status waarden:")
                important = [
                    ('tcp_ip_connection', 'TCP-IP Verbinding'),
                    ('power_on', 'Power Status'),
                    ('automatic_mode_on', 'Automatische Mode'),
                    ('manual_mode_on', 'Handmatige Mode'),
                    ('mobile_quantity', 'Aantal Mobiles')
                ]
                
                for key, label in important:
                    if key in status:
                        value = status[key]
                        if isinstance(value, bool):
                            value = "ON" if value else "OFF"
                        print(f"      {label}: {value}")
            
            client.disconnect()
            return True
        else:
            print("   ❌ Geen status response ontvangen")
            client.disconnect()
            return False
            
    except Exception as e:
        print(f"   ❌ PLC protocol test fout: {e}")
        return False

def check_firewall_and_vpn():
    """Check firewall en VPN gerelateerde issues"""
    print(f"\n4. Firewall & VPN Checks:")
    
    # Check Windows Firewall status
    print("   a) Windows Firewall status:")
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if 'ON' in result.stdout:
            print("   ⚠️  Windows Firewall is ACTIEF")
            print("      → Mogelijk blokkeert firewall uitgaande TCP verbindingen")
            print("      → Check firewall regels voor poort 2000")
        else:
            print("   ✅ Windows Firewall lijkt uitgeschakeld")
            
    except Exception as e:
        print(f"   ❌ Kan firewall status niet checken: {e}")
    
    # Check network adapters (VPN indicatie)
    print("   b) Netwerk adapters (VPN check):")
    try:
        result = subprocess.run(
            ['ipconfig', '/all'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        vpn_keywords = ['VPN', 'TAP', 'OpenVPN', 'Cisco', 'Tunnel']
        found_vpn = False
        
        for keyword in vpn_keywords:
            if keyword.lower() in result.stdout.lower():
                found_vpn = True
                print(f"   🔍 VPN adapter gevonden: {keyword}")
        
        if found_vpn:
            print("   ✅ VPN verbinding gedetecteerd")
        else:
            print("   ⚠️  Geen VPN adapter gedetecteerd")
            
    except Exception as e:
        print(f"   ❌ Kan network adapters niet checken: {e}")

def advanced_port_scan(host, port):
    """Geavanceerde poort scan met timing info"""
    print(f"\n5. Geavanceerde Poort Analyse:")
    
    print(f"   Testing verbinding timing naar {host}:{port}...")
    
    success_count = 0
    total_tests = 5
    times = []
    
    for i in range(total_tests):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            start_time = time.time()
            result = sock.connect_ex((host, port))
            end_time = time.time()
            
            sock.close()
            
            if result == 0:
                success_count += 1
                connect_time = (end_time - start_time) * 1000
                times.append(connect_time)
                print(f"   Test {i+1}: ✅ Verbonden in {connect_time:.0f}ms")
            else:
                print(f"   Test {i+1}: ❌ Mislukt (Error: {result})")
            
            time.sleep(0.5)  # Korte pauze tussen tests
            
        except Exception as e:
            print(f"   Test {i+1}: ❌ Exception: {e}")
    
    if success_count > 0:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n   📊 Resultaten van {total_tests} tests:")
        print(f"      Succesvol: {success_count}/{total_tests} ({success_count/total_tests*100:.0f}%)")
        print(f"      Gemiddelde tijd: {avg_time:.0f}ms")
        print(f"      Min/Max tijd: {min_time:.0f}ms / {max_time:.0f}ms")
        
        if avg_time > 1000:
            print("   ⚠️  Langzame verbindingen - mogelijk VPN/netwerk latency")
        elif success_count < total_tests:
            print("   ⚠️  Inconsistente verbindingen - mogelijk netwerk instabiliteit")
        else:
            print("   ✅ Stabiele en snelle verbindingen")
    else:
        print(f"   ❌ Alle {total_tests} verbindingstests mislukt")

def provide_recommendations(host, port):
    """Geef aanbevelingen op basis van test resultaten"""
    print(f"\n=== AANBEVELINGEN ===")
    print("\n💡 Mogelijke oplossingen om te proberen:")
    
    print("\n1. PLC/Server kant:")
    print("   • Controleer of de Mobile Racking software draait")
    print("   • Verificeer dat TCP-IP server actief is op poort 2000")
    print("   • Check PLC/server firewall instellingen")
    print("   • Herstart de Mobile Racking service")
    
    print("\n2. Netwerk kant:")
    print("   • Controleer VPN verbinding stabiliteit")
    print("   • Test vanaf een andere machine op hetzelfde netwerk")
    print("   • Ping de PLC meerdere keren om packetverlies te checken")
    print("   • Controleer of er port forwarding nodig is")
    
    print("\n3. Windows Firewall:")
    print("   • Tijdelijk uitschakelen voor test:")
    print("     netsh advfirewall set allprofiles state off")
    print("   • Of maak regel voor uitgaande TCP verbindingen naar poort 2000")
    
    print("\n4. Alternatieve tests:")
    print(f"   • Probeer telnet: telnet {host} {port}")
    print(f"   • Gebruik netcat: nc -v {host} {port}")
    print("   • Test vanaf command line met Python socket")
    
    print("\n5. PLC specifiek:")
    print("   • Controleer PLC configuratie voor TCP-IP module")
    print("   • Verificeer IP adres configuratie op PLC")
    print("   • Check of PLC in RUN mode staat")

def main():
    """Hoofdfunctie voor diagnose"""
    host = "1.1.1.2"
    port = 2000
    
    print("🔍 PLC TCP-IP DIAGNOSE TOOL")
    print("=" * 50)
    
    # Run alle diagnose tests
    network_ok = check_network_basics(host)
    
    if network_ok:
        port_ok = check_port_connectivity(host, port)
        
        if port_ok:
            protocol_ok = test_plc_protocol(host, port)
            
            if protocol_ok:
                print("\n🎉 ALLE TESTS GESLAAGD!")
                print("PLC is bereikbaar en protocol werkt correct.")
            else:
                print("\n⚠️  POORT OPEN MAAR PROTOCOL PROBLEMEN")
                print("Verbinding mogelijk maar PLC reageert niet correct.")
        else:
            print("\n❌ POORT CONNECTIVITEIT PROBLEMEN")
            advanced_port_scan(host, port)
    else:
        print("\n❌ BASIS NETWERK PROBLEMEN")
    
    check_firewall_and_vpn()
    provide_recommendations(host, port)
    
    print(f"\n{'='*50}")
    print("Diagnose voltooid.")

if __name__ == "__main__":
    main()
