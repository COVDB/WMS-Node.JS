#!/bin/bash
# RevPi Connect SE Deployment Script
# Voor IP: 192.168.0.12 | User: pi | Pass: ph82tv

echo "🚀 WMS DEPLOYMENT VOOR REVOLUTION PI CONNECT SE"
echo "=============================================="
echo "Target: pi@192.168.0.12"
echo "PLC Network: 1.1.1.185 → 1.1.1.2"
echo

# Stap 1: Verbinding testen
echo "📡 Stap 1: SSH Verbinding testen..."
ssh -o ConnectTimeout=5 pi@192.168.0.12 "echo 'SSH verbinding OK!' && hostname && uname -a"

if [ $? -ne 0 ]; then
    echo "❌ SSH verbinding gefaald. Check:"
    echo "   - Is RevPi bereikbaar op 192.168.0.12?"
    echo "   - Zijn SSH credentials correct? (pi/ph82tv)"
    exit 1
fi

# Stap 2: System prep
echo "🔧 Stap 2: System voorbereiden..."
ssh pi@192.168.0.12 << 'EOF'
    # Update systeem
    sudo apt update && sudo apt upgrade -y
    
    # Ruimte vrijmaken
    sudo apt autoremove --purge -y
    sudo apt autoclean
    
    # Docker installeren (als niet aanwezig)
    if ! command -v docker &> /dev/null; then
        echo "🐳 Docker installeren..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker pi
        sudo systemctl enable docker
        sudo systemctl start docker
        rm get-docker.sh
    fi
    
    # Docker Compose installeren
    if ! command -v docker-compose &> /dev/null; then
        echo "🔧 Docker Compose installeren..."
        sudo pip3 install docker-compose
    fi
    
    # Project directory maken
    mkdir -p /home/pi/wms
    
    echo "✅ System prep voltooid!"
EOF

# Stap 3: Bestanden uploaden
echo "📦 Stap 3: Project bestanden uploaden..."
scp -r ./* pi@192.168.0.12:/home/pi/wms/

# Stap 4: Deployment uitvoeren
echo "🚀 Stap 4: WMS applicatie deployen..."
ssh pi@192.168.0.12 << 'EOF'
    cd /home/pi/wms
    
    # Build en start containers
    docker-compose down 2>/dev/null || true
    docker-compose up -d --build
    
    # Wacht op startup
    echo "⏳ Wachten op container startup..."
    sleep 30
    
    # Status check
    docker ps
    docker logs wms-streamlit --tail 20
    
    echo "✅ Deployment voltooid!"
EOF

# Stap 5: Firewall configureren
echo "🔥 Stap 5: Firewall configureren..."
ssh pi@192.168.0.12 << 'EOF'
    # UFW configureren
    sudo ufw --force enable
    sudo ufw allow ssh
    sudo ufw allow 8502/tcp   # Streamlit
    sudo ufw allow 2000/tcp   # TCP Server
    sudo ufw allow from 1.1.1.0/24  # PLC Network
    
    sudo ufw status
    echo "✅ Firewall geconfigureerd!"
EOF

# Stap 6: Health check
echo "🏥 Stap 6: Health check uitvoeren..."
ssh pi@192.168.0.12 << 'EOF'
    cd /home/pi/wms
    
    # Container status
    echo "📊 Container Status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Health check
    echo "🏥 Health Check:"
    sleep 10
    curl -f http://localhost:8502/_stcore/health && echo "✅ Streamlit Health OK" || echo "❌ Streamlit Health Failed"
    
    # PLC connectivity test
    echo "🔗 PLC Connectivity Test:"
    docker exec wms-streamlit python -c "
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    result = s.connect_ex(('1.1.1.2', 2000))
    s.close()
    if result == 0:
        print('✅ PLC 1.1.1.2:2000 bereikbaar')
    else:
        print('❌ PLC 1.1.1.2:2000 niet bereikbaar')
except Exception as e:
    print(f'❌ PLC test error: {e}')
"
EOF

echo
echo "🎉 DEPLOYMENT VOLTOOID!"
echo "======================="
echo "🌐 Streamlit UI: http://192.168.0.12:8502"
echo "🔧 SSH Access: ssh pi@192.168.0.12"
echo "📊 Container Logs: ssh pi@192.168.0.12 'docker logs -f wms-streamlit'"
echo
echo "📋 VOLGENDE STAPPEN:"
echo "1. Open http://192.168.0.12:8502 in browser"
echo "2. Test PLC connectie vanuit Streamlit UI"
echo "3. Configureer auto-start (systemd service)"
echo "4. Setup monitoring & alerting"
echo
