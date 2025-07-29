#!/bin/bash
# RevPi Manual Setup Script
# Voer dit uit op de RevPi zelf via SSH

echo "🚀 REVPI WMS SETUP - HANDMATIGE INSTALLATIE"
echo "==========================================="

# Stap 1: System update
echo "🔄 Systeem updaten..."
sudo apt update && sudo apt upgrade -y

# Stap 2: Python en pip installeren
echo "🐍 Python environment setup..."
sudo apt install -y python3 python3-pip python3-venv git curl

# Stap 3: Project directory maken
echo "📁 Project directory aanmaken..."
mkdir -p /home/pi/wms
cd /home/pi/wms

# Stap 4: Virtual environment maken
echo "🏗️ Virtual environment maken..."
python3 -m venv .venv
source .venv/bin/activate

# Stap 5: Dependencies installeren
echo "📦 Dependencies installeren..."
pip install --upgrade pip
pip install streamlit pandas numpy socket-io requests psutil

# Stap 6: Systeem service maken
echo "⚙️ Systemd service maken..."
sudo tee /etc/systemd/system/wms-streamlit.service > /dev/null << 'EOF'
[Unit]
Description=WMS Streamlit Application
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wms
Environment=PATH=/home/pi/wms/.venv/bin
ExecStart=/home/pi/wms/.venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Stap 7: Firewall configureren
echo "🔥 Firewall configureren..."
sudo ufw allow 8502/tcp
sudo ufw allow ssh
sudo ufw --force enable

# Stap 8: Service enablen
echo "🏃 Service enablen..."
sudo systemctl daemon-reload
sudo systemctl enable wms-streamlit

echo "✅ SETUP VOLTOOID!"
echo "Volgende stappen:"
echo "1. Upload je app.py en andere bestanden naar /home/pi/wms/"
echo "2. Start service: sudo systemctl start wms-streamlit"
echo "3. Check status: sudo systemctl status wms-streamlit"
echo "4. Toegang via: http://192.168.0.12:8502"
