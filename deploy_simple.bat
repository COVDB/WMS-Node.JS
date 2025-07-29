@echo off
REM Eenvoudige RevPi deployment zonder Docker
REM Voor directe Python installatie

echo 🚀 REVPI EENVOUDIGE DEPLOYMENT
echo ============================
echo Target: pi@192.168.0.12
echo.

echo 📡 Stap 1: Verbinding testen...
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no pi@192.168.0.12 "echo 'RevPi bereikbaar!' && hostname"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Verbinding gefaald
    pause
    exit /b 1
)

echo 📦 Stap 2: Setup script uploaden...
scp revpi_manual_setup.sh pi@192.168.0.12:/home/pi/
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Upload gefaald
    pause
    exit /b 1
)

echo 🔧 Stap 3: System setup uitvoeren...
ssh pi@192.168.0.12 "chmod +x /home/pi/revpi_manual_setup.sh && /home/pi/revpi_manual_setup.sh"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Setup gefaald
    pause
    exit /b 1
)

echo 📁 Stap 4: Project bestanden uploaden...
scp app.py requirements.txt wms_protocol.py tcp_client.py pi@192.168.0.12:/home/pi/wms/
scp -r utils pi@192.168.0.12:/home/pi/wms/
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Bestanden upload gefaald
    pause
    exit /b 1
)

echo 🚀 Stap 5: Service starten...
ssh pi@192.168.0.12 "sudo systemctl start wms-streamlit && sudo systemctl status wms-streamlit --no-pager"

echo.
echo 🎉 DEPLOYMENT VOLTOOID!
echo =======================
echo 🌐 Streamlit UI: http://192.168.0.12:8502
echo 📊 Service Status: ssh pi@192.168.0.12 'sudo systemctl status wms-streamlit'
echo 📋 Logs: ssh pi@192.168.0.12 'journalctl -u wms-streamlit -f'
echo.
echo Test nu: http://192.168.0.12:8502
pause
