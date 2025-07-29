"""
PLC Port Scanner & Connection Tester
Tool om verschillende poorten en configuraties te testen
"""

import socket
import time
from concurrent.futures import ThreadPoolExecutor
import argparse

def test_port(host, port, timeout=5):
    """Test een specifieke poort"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()
        
        sock.close()
        
        if result == 0:
            return port, True, (end_time - start_time) * 1000
        else:
            return port, False, None
            
    except Exception:
        return port, False, None

def scan_common_ports(host):
    """Scan veel gebruikte industriële poorten"""
    print(f"🔍 Scanning veelgebruikte industriële poorten op {host}...")
    
    # Veel gebruikte poorten voor PLC/SCADA systemen
    common_ports = [
        20, 21,        # FTP
        22,            # SSH
        23,            # Telnet
        25,            # SMTP
        53,            # DNS
        80,            # HTTP
        102,           # S7 (Siemens)
        135,           # RPC
        443,           # HTTPS
        502,           # Modbus
        1883,          # MQTT
        2000,          # Common industrial
        2001, 2002,    # Related ports
        4840,          # OPC UA
        5000, 5001,    # UPnP, misc
        8080,          # HTTP alt
        9600,          # Common serial-to-TCP
        10000, 10001,  # Network Data Management
        44818          # EtherNet/IP
    ]
    
    print(f"Testing {len(common_ports)} poorten...")
    
    # Parallel testing voor snelheid
    open_ports = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(test_port, host, port, 3) for port in common_ports]
        
        for i, future in enumerate(futures):
            port, is_open, response_time = future.result()
            
            if is_open:
                open_ports.append((port, response_time))
                print(f"✅ Poort {port}: OPEN ({response_time:.0f}ms)")
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"   Progress: {i+1}/{len(common_ports)} poorten getest")
    
    print(f"\n📊 Resultaten:")
    if open_ports:
        print(f"   {len(open_ports)} open poorten gevonden:")
        for port, response_time in sorted(open_ports):
            print(f"   • Poort {port} ({response_time:.0f}ms)")
    else:
        print("   ❌ Geen open poorten gevonden")
        print("   Dit kan betekenen:")
        print("     - Host is niet bereikbaar")
        print("     - Alle poorten zijn gesloten/gefilterd")
        print("     - Firewall blokkeert verbindingen")
    
    return open_ports

def test_port_range(host, start_port, end_port):
    """Test een range van poorten rond 2000"""
    print(f"\n🔍 Testing poort range {start_port}-{end_port} op {host}...")
    
    open_ports = []
    for port in range(start_port, end_port + 1):
        port_num, is_open, response_time = test_port(host, port, 2)
        
        if is_open:
            open_ports.append((port_num, response_time))
            print(f"✅ Poort {port_num}: OPEN ({response_time:.0f}ms)")
        
        # Kleine delay om netwerk niet te overbelasten
        time.sleep(0.1)
    
    if not open_ports:
        print(f"❌ Geen open poorten gevonden in range {start_port}-{end_port}")
    
    return open_ports

def test_alternative_ips():
    """Test alternatieve IP adressen die mogelijk gebruikt worden"""
    print(f"\n🔍 Testing alternatieve IP adressen voor Mobile Racking...")
    
    # Mogelijke IP adressen voor Mobile Racking systemen
    test_ips = [
        "1.1.1.2",      # Oorspronkelijk
        "1.1.1.1",      # Gateway/Router
        "1.1.1.10",     # Alternatief
        "192.168.1.2",  # Standaard LAN
        "192.168.1.100",
        "192.168.0.2",
        "10.0.0.2",     # Privé netwerk
        "172.16.0.2",
    ]
    
    working_ips = []
    
    for ip in test_ips:
        print(f"   Testing {ip}:2000...")
        
        port_num, is_open, response_time = test_port(ip, 2000, 5)
        
        if is_open:
            working_ips.append((ip, response_time))
            print(f"   ✅ {ip}:2000 OPEN ({response_time:.0f}ms)")
        else:
            print(f"   ❌ {ip}:2000 gesloten/timeout")
    
    if working_ips:
        print(f"\n🎉 Werkende IP adressen gevonden:")
        for ip, response_time in working_ips:
            print(f"   • {ip}:2000 ({response_time:.0f}ms)")
    else:
        print(f"\n❌ Geen werkende IP adressen gevonden op poort 2000")
    
    return working_ips

def network_traceroute(host):
    """Eenvoudige traceroute om netwerk path te checken"""
    print(f"\n🛣️  Network path naar {host}...")
    
    try:
        import subprocess
        result = subprocess.run(
            ['tracert', '-h', '10', host], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            hop_count = 0
            for line in lines:
                if 'ms' in line and '*' not in line:
                    hop_count += 1
            
            print(f"   Netwerk hops naar {host}: {hop_count}")
            if hop_count > 10:
                print(f"   ⚠️  Veel hops - mogelijk complexe netwerk route via VPN")
        else:
            print(f"   ❌ Traceroute mislukt")
            
    except Exception as e:
        print(f"   ❌ Traceroute error: {e}")

def main():
    """Hoofdfunctie"""
    parser = argparse.ArgumentParser(description='PLC Port Scanner & Connection Tester')
    parser.add_argument('--host', default='1.1.1.2', help='Target host IP')
    parser.add_argument('--quick', action='store_true', help='Only test common ports')
    parser.add_argument('--range', action='store_true', help='Test port range around 2000')
    parser.add_argument('--alt-ips', action='store_true', help='Test alternative IP addresses')
    
    args = parser.parse_args()
    
    print("🔍 PLC CONNECTION TESTER")
    print("=" * 40)
    
    host = args.host
    
    # Basis connectiviteit test
    print(f"Testing basis connectiviteit naar {host}...")
    port_num, is_open, response_time = test_port(host, 2000, 10)
    
    if is_open:
        print(f"✅ SUCCESS: {host}:2000 is OPEN ({response_time:.0f}ms)")
        print("🎉 Je PLC is bereikbaar op de standaard poort!")
        return
    else:
        print(f"❌ FAILED: {host}:2000 is niet bereikbaar")
    
    # Extended testing als basis mislukt
    print(f"\n🔍 Extended testing...")
    
    if not args.quick:
        # Scan common ports
        open_ports = scan_common_ports(host)
        
        if args.range:
            # Test range rond 2000
            range_ports = test_port_range(host, 1990, 2010)
    
    if args.alt_ips:
        # Test alternatieve IPs
        working_ips = test_alternative_ips()
    
    # Network path analysis
    network_traceroute(host)
    
    print(f"\n📋 SAMENVATTING:")
    print(f"   Target: {host}:2000")
    print(f"   Status: ❌ Niet bereikbaar")
    print(f"\n💡 AANBEVELINGEN:")
    print(f"   1. Controleer of Mobile Racking software draait")
    print(f"   2. Verificeer PLC TCP-IP configuratie")
    print(f"   3. Check VPN verbinding stabiliteit")
    print(f"   4. Vraag netwerkbeheerder om firewall/routing te checken")

if __name__ == "__main__":
    main()
