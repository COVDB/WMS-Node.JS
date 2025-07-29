@echo off
REM Windows Deployment Script voor RevPi Connect SE
REM Target: pi@192.168.0.12

echo 🚀 WMS DEPLOYMENT VOOR REVOLUTION PI CONNECT SE
echo ==============================================
echo Target: pi@192.168.0.12
echo PLC Network: 1.1.1.185 → 1.1.1.2
echo.

REM Check if we have WSL/SSH available
where ssh >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ SSH niet gevonden. Installeer:
    echo    - Windows Subsystem for Linux ^(WSL^)
    echo    - OpenSSH Client
    echo    - Of gebruik PuTTY/WinSCP
    pause
    exit /b 1
)

echo 📡 Stap 1: SSH Verbinding testen...
ssh -o ConnectTimeout=5 pi@192.168.0.12 "echo 'SSH verbinding OK!' && hostname && uname -a"
if %ERRORLEVEL% NEQ 0 (
    echo ❌ SSH verbinding gefaald. Check:
    echo    - Is RevPi bereikbaar op 192.168.0.12?
    echo    - Zijn SSH credentials correct? ^(pi/ph82tv^)
    pause
    exit /b 1
)

echo 📦 Stap 2: Project bestanden uploaden via SCP...
scp -r .\* pi@192.168.0.12:/home/pi/wms/
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Bestand upload gefaald
    pause
    exit /b 1
)

echo 🔧 Stap 3: System setup en Docker installatie...
ssh pi@192.168.0.12 "cd /home/pi/wms && chmod +x deploy_to_revpi.sh && ./deploy_to_revpi.sh"

echo.
echo 🎉 DEPLOYMENT VOLTOOID!
echo =======================
echo 🌐 Streamlit UI: http://192.168.0.12:8502
echo 🔧 SSH Access: ssh pi@192.168.0.12
echo.
echo 📋 Test de deployment:
echo 1. Open http://192.168.0.12:8502 in browser
echo 2. Login en test PLC connectie
echo 3. Controleer live monitoring functionaliteit
echo.
pause
