"""
🎯 REVPI SPECIFIC DEPLOYMENT PLAN
Revolution Pi Connect SE - 192.168.0.12

📋 SYSTEEM SPECIFICATIES ONTVANGEN:
"""

print("🔧 REVPI CONFIGURATIE DETAILS:")
print("=" * 60)
print("🖥️  **Model:** Revolution Pi Connect SE")
print("🌐 **Management IP:** 192.168.0.12 (eth0)")
print("🏭 **PLC Network IP:** 1.1.1.185/24 (eth1)")
print("👤 **Toegang:** SSH - pi@192.168.0.12 (wachtwoord: ph82tv)")
print("💾 **Beschikbare ruimte:** ~1GB vrij van 8GB (uitbreidbaar)")
print("🔗 **PLC/HMI connectie:** eth1 → 1.1.1.2:2000/2001")
print()

print("🎯 OPTIMALE DEPLOYMENT STRATEGIE:")
print("=" * 60)
print("✅ **Docker Container Deployment** (Aanbevolen)")
print("   → Isolatie en eenvoudige management")
print("   → Minimale resource footprint")
print("   → Easy updates en rollbacks")
print()

print("🏗️ DEPLOYMENT ARCHITECTUUR:")
print("=" * 60)
print("┌─────────────────────────────────────────────────────────┐")
print("│                REVOLUTION PI CONNECT SE                 │")
print("│                   192.168.0.12                         │")
print("├─────────────────┬───────────────────────────────────────┤")
print("│ eth0: Management│ eth1: PLC Network                     │")
print("│ 192.168.0.12    │ 1.1.1.185/24                        │")
print("│                 │                                       │")
print("│ [Docker]        │ ┌─────────────────────────────────┐   │")
print("│ ┌─────────────┐ │ │        PLC/HMI NETWORK          │   │")
print("│ │ WMS Container│ │ │                                 │   │")
print("│ │   :8502     │ │ │  PLC: 1.1.1.2:2000/2001       │   │")
print("│ │   :2000     │◄┼─┤  HMI: 1.1.1.2                 │   │")
print("│ └─────────────┘ │ │                                 │   │")
print("└─────────────────┴─┤                                 │   │")
print("                    └─────────────────────────────────┘   │")
print("└─────────────────────────────────────────────────────────┘")
print()

print("📦 DOCKER DEPLOYMENT STAPPEN:")
print("=" * 60)
print("**Stap 1: SSH Verbinding maken**")
print("   ssh pi@192.168.0.12")
print("   # Wachtwoord: ph82tv")
print()

print("**Stap 2: Docker installeren (indien niet aanwezig)**")
print("   curl -fsSL https://get.docker.com -o get-docker.sh")
print("   sudo sh get-docker.sh")
print("   sudo usermod -aG docker pi")
print("   sudo systemctl enable docker")
print()

print("**Stap 3: Project bestanden uploaden**")
print("   # Via SCP vanaf development machine:")
print("   scp -r c:\\WMS-Node.JS\\* pi@192.168.0.12:/home/pi/wms/")
print()

print("**Stap 4: Dockerfile maken op RevPi**")
dockerfile_content = '''
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application files
COPY . .

# Expose ports
EXPOSE 8502 2000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8502/_stcore/health || exit 1

# Start command
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8502"]
'''
print("   # Dockerfile inhoud:")
for line in dockerfile_content.strip().split('\n'):
    print(f"   {line}")
print()

print("**Stap 5: Docker Compose configuratie**")
compose_content = '''
version: '3.8'

services:
  wms-app:
    build: .
    container_name: wms-streamlit
    ports:
      - "8502:8502"    # Streamlit Web UI
      - "2000:2000"    # TCP Server (optioneel)
    environment:
      - PLC_IP=1.1.1.2
      - PLC_PORT=2000
      - HMI_PORT=2001
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    networks:
      - wms-network
    
networks:
  wms-network:
    driver: bridge
'''
print("   # docker-compose.yml:")
for line in compose_content.strip().split('\n'):
    print(f"   {line}")
print()

print("**Stap 6: Deployment uitvoeren**")
print("   cd /home/pi/wms")
print("   docker-compose up -d --build")
print()

print("**Stap 7: Firewall configuratie**")
print("   sudo ufw allow 8502/tcp  # Streamlit")
print("   sudo ufw allow 2000/tcp  # TCP Server")
print("   sudo ufw allow from 1.1.1.0/24  # PLC Network")
print()

print("🔧 NETWERK CONFIGURATIE:")
print("=" * 60)
print("**PLC Verbinding (eth1 - 1.1.1.185):**")
print("   → Kan direct communiceren met PLC (1.1.1.2)")
print("   → Netwerkroute al geconfigureerd")
print("   → Geen extra routing nodig")
print()

print("**Web Toegang (eth0 - 192.168.0.12):**")
print("   → Streamlit UI: http://192.168.0.12:8502")
print("   → Management: ssh pi@192.168.0.12")
print("   → Logs: docker logs wms-streamlit")
print()

print("⚙️ CONFIGURATIE AANPASSINGEN:")
print("=" * 60)
print("**app.py configuratie voor RevPi:**")
app_config = '''
# Netwerk configuratie voor RevPi deployment
PLC_IP = "1.1.1.2"      # PLC adres via eth1
PLC_PORT = 2000         # TCP poort
HMI_PORT = 2001         # HMI poort
BIND_IP = "0.0.0.0"     # Bind aan alle interfaces
WEB_PORT = 8502         # Streamlit poort

# RevPi specifieke instellingen
INTERFACE_ETH1 = "1.1.1.185"  # RevPi IP op PLC network
INTERFACE_ETH0 = "192.168.0.12"  # RevPi management IP
'''
print(app_config)

print("🚀 DEPLOYMENT COMMANDO'S:")
print("=" * 60)
print("**1. Verbinding maken:**")
print("   ssh pi@192.168.0.12")
print()
print("**2. Ruimte vrijmaken (indien nodig):**")
print("   sudo apt autoremove --purge")
print("   sudo apt autoclean")
print("   docker system prune -af")
print()
print("**3. Project deployen:**")
print("   git clone <your-repo> /home/pi/wms")
print("   cd /home/pi/wms")
print("   docker-compose up -d --build")
print()
print("**4. Status controleren:**")
print("   docker ps")
print("   docker logs wms-streamlit")
print("   curl http://localhost:8502")
print()

print("📊 MONITORING & MAINTENANCE:")
print("=" * 60)
print("**Log monitoring:**")
print("   docker logs -f wms-streamlit")
print("   tail -f /home/pi/wms/logs/wms.log")
print()
print("**Health checks:**")
print("   docker exec wms-streamlit python test_connection.py")
print("   docker exec wms-streamlit python diagnose_plc.py")
print()
print("**Updates:**")
print("   git pull")
print("   docker-compose down")
print("   docker-compose up -d --build")
print()

print("🔐 BEVEILIGING:")
print("=" * 60)
print("✅ **SSH toegang beveiligd met key-based auth (aanbevolen)**")
print("✅ **UFW firewall geconfigureerd**")
print("✅ **Docker container isolatie**")
print("✅ **Netwerkscheiding tussen management en PLC**")
print()

print("⚡ PERFORMANCE OPTIMALISATIE:")
print("=" * 60)
print("**Resource limieten:**")
print("   - Memory limit: 512MB (aanpasbaar)")
print("   - CPU limit: 1 core")
print("   - Storage: <500MB voor app + logs")
print()
print("**Auto-restart configuratie:**")
print("   - Container restart: unless-stopped")
print("   - Health checks: elke 30 seconden")
print("   - Log rotation: automatisch")
print()

print("🎯 TOEGANG NA DEPLOYMENT:")
print("=" * 60)
print("🌐 **Streamlit Web UI:**")
print("   http://192.168.0.12:8502")
print()
print("🔧 **SSH Management:**")
print("   ssh pi@192.168.0.12")
print()
print("📊 **Container Management:**")
print("   docker exec -it wms-streamlit bash")
print()
print("📈 **Live Monitoring:**")
print("   - PLC Status: Real-time via eth1")
print("   - Web Access: Via eth0")
print("   - Logs: Centralized in Docker")
print()

print("=" * 60)
print("🚀 READY VOOR DEPLOYMENT!")
print("💪 OPTIMAAL CONFIGURED VOOR JOUW REVPI!")
print("🏭 INDUSTRIAL-GRADE WMS MONITORING!")
print("=" * 60)
