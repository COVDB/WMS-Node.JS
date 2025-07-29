"""
WMS Mobile Racking TCP-IP Communicatie Streamlit App
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List

# Local imports
from tcp_client import TCPClient
from wms_protocol import WMS_DATA_STRUCTURE, WMSCommands, get_status_description
from utils.data_parser import (
    format_hex_data, parse_lighting_rules, validate_status_data, 
    format_timestamp
)
from utils.logger import wms_logger

# Page config
st.set_page_config(
    page_title="WMS Mobile Racking Controller",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'client' not in st.session_state:
    st.session_state.client = None
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'status_history' not in st.session_state:
    st.session_state.status_history = []
if 'last_status' not in st.session_state:
    st.session_state.last_status = {}
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

def create_connection():
    """Maak verbinding met Mobile Racking controller"""
    host = st.session_state.get('host', '1.1.1.2')
    port = st.session_state.get('port', 2000)
    
    # Progress bar en status updates
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔍 Initialiseren verbinding...")
        progress_bar.progress(10)
        
        if st.session_state.client:
            st.session_state.client.disconnect()
        
        status_text.text(f"🔌 Verbinden naar {host}:{port}...")
        progress_bar.progress(30)
        
        st.session_state.client = TCPClient(host, port)
        
        status_text.text("📡 TCP handshake...")
        progress_bar.progress(60)
        
        success = st.session_state.client.connect()
        progress_bar.progress(100)
        
        if success:
            st.session_state.connected = True
            status_text.empty()
            progress_bar.empty()
            st.success(f"✅ Verbonden met {host}:{port}")
            wms_logger.log_connection(host, port, True)
            
            # Test direct een status request
            with st.spinner("📊 Testing verbinding met status request..."):
                status = st.session_state.client.get_status()
                if status:
                    st.info("🎉 Status succesvol ontvangen - verbinding werkt!")
                else:
                    st.warning("⚠️ Verbinding OK maar geen status ontvangen")
        else:
            st.session_state.connected = False
            status_text.empty()
            progress_bar.empty()
            
            # Detailiere error message
            st.error(f"❌ Verbinding mislukt naar {host}:{port}")
            
            # Geef specifieke diagnose tips
            with st.expander("🔍 Diagnose en oplossingen", expanded=True):
                st.markdown("""
                **Mogelijke oorzaken:**
                
                1. **PLC Service niet actief**
                   - Mobile Racking software draait niet
                   - TCP-IP server module niet gestart
                   - PLC in STOP mode
                
                2. **Netwerk problemen**
                   - VPN verbinding instabiel
                   - Firewall blokkeert poort 2000
                   - Port forwarding niet geconfigureerd
                
                3. **Configuratie problemen**
                   - Verkeerd IP adres
                   - Verkeerde poort nummer
                   - PLC TCP-IP module verkeerd geconfigureerd
                
                **Wat te doen:**
                1. Controleer of je de PLC kan pingen: `ping 1.1.1.2`
                2. Check of de Mobile Racking software draait op de PLC
                3. Vraag PLC beheerder om TCP-IP server status te checken
                4. Test vanaf een andere machine op hetzelfde netwerk
                """)
                
                # Test buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🏓 Test Ping"):
                        with st.spinner("Pinging..."):
                            # Dit zou je kunnen implementeren met subprocess
                            st.info("Ping test functie - implementeer in terminal")
                
                with col2:
                    if st.button("🔍 Uitgebreide Diagnose"):
                        st.info("Run 'python diagnose_plc.py' in terminal voor volledige diagnose")
            
            wms_logger.log_connection(host, port, False)
            
    except Exception as e:
        st.session_state.connected = False
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Onverwachte fout: {e}")
        
        with st.expander("📋 Technische details"):
            st.code(str(e))
            st.markdown("**Debug info:** Check logs voor meer details")

def disconnect():
    """Verbreek verbinding"""
    if st.session_state.client:
        st.session_state.client.disconnect()
    st.session_state.connected = False
    st.session_state.client = None
    st.info("Verbinding verbroken")

def get_system_status():
    """Haal systeem status op"""
    if not st.session_state.connected or not st.session_state.client:
        return None
    
    try:
        status = st.session_state.client.get_status()
        if status:
            # Voeg timestamp toe
            status['timestamp'] = datetime.now()
            
            # Voeg toe aan historie
            st.session_state.status_history.append(status.copy())
            
            # Bewaar alleen laatste 100 entries
            if len(st.session_state.status_history) > 100:
                st.session_state.status_history = st.session_state.status_history[-100:]
            
            st.session_state.last_status = status
            return status
        else:
            st.error("Geen status ontvangen")
            return None
            
    except Exception as e:
        st.error(f"Fout bij ophalen status: {e}")
        return None

def send_command(command: int):
    """Verzend command naar controller"""
    if not st.session_state.connected or not st.session_state.client:
        st.error("Geen verbinding")
        return False
    
    try:
        response = st.session_state.client.send_command(command)
        if response:
            st.success(f"Command {command} verzonden")
            wms_logger.log_command(command, len(response))
            return True
        else:
            st.error(f"Command {command} mislukt")
            wms_logger.log_command(command, None)
            return False
            
    except Exception as e:
        st.error(f"Fout bij verzenden command: {e}")
        return False

def render_sidebar():
    """Render zijbalk met verbinding configuratie"""
    st.sidebar.header("🔌 Verbinding")
    
    # Verbinding configuratie
    host = st.sidebar.text_input("IP Adres", value="1.1.1.2", key="host")
    
    # Poort selectie met detectie
    st.sidebar.write("**Poort Configuratie:**")
    port_option = st.sidebar.radio(
        "Selecteer poort:",
        ["2001 (Detected ✅)", "2000 (Original)", "Custom"],
        key="port_option"
    )
    
    if port_option == "2001 (Detected ✅)":
        port = 2001
        st.sidebar.success("Poort 2001 gedetecteerd als open!")
    elif port_option == "2000 (Original)":
        port = 2000
        st.sidebar.warning("Poort 2000 lijkt gesloten")
    else:  # Custom
        port = st.sidebar.number_input("Custom poort:", min_value=1, max_value=65535, value=2001)
    
    st.session_state.port = port
    
    # Connection status indicator
    if st.session_state.connected:
        st.sidebar.success(f"🟢 Verbonden met {host}:{port}")
    else:
        st.sidebar.error("🔴 Niet verbonden")
    
    # Verbinding knoppen
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Verbinden", type="primary", disabled=st.session_state.connected):
            create_connection()
    
    with col2:
        if st.button("Verbreken", disabled=not st.session_state.connected):
            disconnect()
    
    st.sidebar.divider()
    
    # Quick port scan
    st.sidebar.header("🔍 Diagnose")
    if st.button("Port Scan", help="Scan open poorten op de PLC"):
        with st.spinner("Scanning poorten..."):
            # Quick port test voor diagnose
            from port_scanner import test_port
            test_ports = [2000, 2001, 2002, 102, 4840]
            open_ports = []
            
            for p in test_ports:
                _, is_open, response_time = test_port(host, p, 3)
                if is_open:
                    open_ports.append((p, response_time))
            
            if open_ports:
                st.sidebar.success(f"Open poorten gevonden:")
                for p, rt in open_ports:
                    st.sidebar.write(f"• Poort {p} ({rt:.0f}ms)")
            else:
                st.sidebar.error("Geen open poorten gevonden")
    
    st.sidebar.divider()
    
    # Auto refresh
    st.sidebar.header("⚙️ Instellingen")
    auto_refresh = st.sidebar.checkbox(
        "Auto refresh (5s)",
        value=st.session_state.auto_refresh,
        key="auto_refresh"
    )
    
    if auto_refresh and st.session_state.connected:
        time.sleep(5)
        st.rerun()

def render_status_overview(status: Dict[str, Any]):
    """Render status overzicht"""
    st.header("📊 Systeem Status")
    
    # Validatie
    validation = validate_status_data(status)
    
    # Alerts
    if validation['errors']:
        for error in validation['errors']:
            st.error(f"🚨 {error}")
    
    if validation['warnings']:
        for warning in validation['warnings']:
            st.warning(f"⚠️ {warning}")
    
    # Status metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tcp_status = "🟢 OK" if status.get('tcp_ip_connection', False) else "🔴 NOK"
        st.metric("TCP-IP Verbinding", tcp_status)
    
    with col2:
        power_status = "🟢 ON" if status.get('power_on', False) else "🔴 OFF"
        st.metric("Power Status", power_status)
    
    with col3:
        mode = "Auto" if status.get('automatic_mode_on', False) else "Manual"
        st.metric("Mode", mode)
    
    with col4:
        mobile_qty = status.get('mobile_quantity', 0)
        st.metric("Mobile Quantity", mobile_qty)

def render_detailed_status(status: Dict[str, Any]):
    """Render gedetailleerde status tabel"""
    st.header("📋 Gedetailleerde Status")
    
    # Maak DataFrame
    status_data = []
    descriptions = get_status_description(status)
    
    for key, value in status.items():
        if key != 'timestamp':
            field_info = WMS_DATA_STRUCTURE.get(key)
            status_data.append({
                'Parameter': key.replace('_', ' ').title(),
                'Waarde': descriptions.get(key, str(value)),
                'Type': field_info.data_type.value if field_info else 'Unknown',
                'Offset': str(field_info.offset) if field_info else 'N/A',
                'Beschrijving': field_info.comment if field_info else 'N/A'
            })
    
    df = pd.DataFrame(status_data)
    
    # Filter opties
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("Filter op type:", ["Alle", "Bool", "Byte", "DWord"])
    with col2:
        show_only_active = st.checkbox("Alleen actieve waardes")
    
    # Apply filters
    if filter_type != "Alle":
        df = df[df['Type'] == filter_type]
    
    if show_only_active:
        df = df[df['Waarde'].isin(['OK', 'True']) | df['Waarde'].str.isdigit()]
    
    # Display table
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_lighting_control(status: Dict[str, Any]):
    """Render lighting controle interface"""
    st.header("💡 Lighting Control")
    
    # Parse huidige lighting rules
    lighting_rules = status.get('lighting_rules', 0)
    active_aisles = parse_lighting_rules(lighting_rules)
    
    st.write(f"Actieve aisles: {', '.join(map(str, active_aisles)) if active_aisles else 'Geen'}")
    
    # Aisle selectie (1-32)
    col1, col2 = st.columns(2)
    
    with col1:
        selected_aisles = st.multiselect(
            "Selecteer aisles om te activeren:",
            options=list(range(1, 33)),
            default=active_aisles,
            key="lighting_aisles"
        )
    
    with col2:
        if st.button("Update Lighting", type="primary"):
            # Dit zou een custom command implementation vereisen
            st.info("Lighting update functionaliteit nog niet geïmplementeerd")

def render_command_interface():
    """Render command interface"""
    st.header("🎛️ Command Interface")
    
    # Voorgedefinieerde commands
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Basis Commands")
        if st.button("Status Request"):
            send_command(WMSCommands.STATUS_REQUEST)
        if st.button("Start Operation"):
            send_command(WMSCommands.START_OPERATION)
        if st.button("Stop Operation"):
            send_command(WMSCommands.STOP_OPERATION)
    
    with col2:
        st.subheader("Mode Commands")
        if st.button("Set Automatic Mode"):
            send_command(WMSCommands.SET_AUTOMATIC_MODE)
        if st.button("Set Manual Mode"):
            send_command(WMSCommands.SET_MANUAL_MODE)
        if st.button("Set Night Mode"):
            send_command(WMSCommands.SET_NIGHT_MODE)
    
    with col3:
        st.subheader("Mobile Commands")
        if st.button("Release Mobiles"):
            send_command(WMSCommands.RELEASE_MOBILES)
        if st.button("Lock Mobiles"):
            send_command(WMSCommands.LOCK_MOBILES)
    
    st.divider()
    
    # Custom command
    st.subheader("Custom Command")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        custom_command = st.number_input(
            "Command nummer (0-65535):",
            min_value=0,
            max_value=65535,
            value=0
        )
    
    with col2:
        if st.button("Verzend"):
            send_command(custom_command)

def render_history_chart():
    """Render status historie grafiek"""
    st.header("📈 Status Historie")
    
    if not st.session_state.status_history:
        st.info("Geen historie data beschikbaar")
        return
    
    # Maak DataFrame van historie
    history_df = pd.DataFrame(st.session_state.status_history)
    
    # Selecteer parameters om te plotten
    numeric_params = [
        'mobile_quantity', 'counter_lift_track_inside', 
        'stow_mobile_racking_major', 'stow_mobile_racking_minor'
    ]
    
    selected_param = st.selectbox(
        "Selecteer parameter:",
        options=numeric_params,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_param in history_df.columns:
        fig = px.line(
            history_df,
            x='timestamp',
            y=selected_param,
            title=f"{selected_param.replace('_', ' ').title()} over tijd"
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    """Hoofdfunctie"""
    st.title("🏭 WMS Mobile Racking Controller")
    st.markdown("TCP-IP communicatie interface voor Mobile Racking systemen")
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    if st.session_state.connected:
        # Refresh knop
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 Refresh Status"):
                get_system_status()
        
        # Haal status op als we verbonden zijn
        if st.button("📊 Get Status", type="primary") or st.session_state.last_status:
            status = get_system_status()
            
            if status or st.session_state.last_status:
                current_status = status or st.session_state.last_status
                
                # Tabs voor verschillende views
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "Status Overview", "Gedetailleerd", "Lighting Control", 
                    "Commands", "Historie"
                ])
                
                with tab1:
                    render_status_overview(current_status)
                
                with tab2:
                    render_detailed_status(current_status)
                
                with tab3:
                    render_lighting_control(current_status)
                
                with tab4:
                    render_command_interface()
                
                with tab5:
                    render_history_chart()
                
                # Timestamp
                if 'timestamp' in current_status:
                    st.sidebar.write(f"Laatste update: {current_status['timestamp'].strftime('%H:%M:%S')}")
    
    else:
        st.info("👆 Maak eerst verbinding via de sidebar")
        
        # Toon live diagnose
        st.header("🔍 PLC Diagnose")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📡 Netwerk Status")
            
            # Test basis connectiviteit
            if st.button("🏓 Test Ping"):
                with st.spinner("Testing ping..."):
                    import subprocess
                    try:
                        result = subprocess.run(
                            ['ping', '1.1.1.2', '-n', '2'], 
                            capture_output=True, text=True, timeout=10
                        )
                        if result.returncode == 0:
                            st.success("✅ Ping succesvol - netwerk OK")
                        else:
                            st.error("❌ Ping mislukt - netwerk probleem")
                    except Exception as e:
                        st.error(f"Ping test fout: {e}")
            
            # Test poorten
            if st.button("🔍 Scan Poorten"):
                with st.spinner("Scanning poorten..."):
                    from port_scanner import test_port
                    
                    test_ports = [
                        (102, "Siemens S7"),
                        (2000, "Mobile Racking (Original)"), 
                        (2001, "Alternative Service"),
                        (4840, "OPC UA")
                    ]
                    
                    port_results = []
                    for port, desc in test_ports:
                        _, is_open, response_time = test_port("1.1.1.2", port, 3)
                        port_results.append((port, desc, is_open, response_time))
                    
                    # Toon resultaten
                    for port, desc, is_open, rt in port_results:
                        if is_open:
                            st.success(f"✅ Poort {port} ({desc}): OPEN ({rt:.0f}ms)")
                        else:
                            st.error(f"❌ Poort {port} ({desc}): GESLOTEN")
        
        with col2:
            st.subheader("🏭 Mobile Racking Status")
            
            st.warning("⚠️ Mobile Racking TCP-IP service niet gedetecteerd")
            
            st.markdown("""
            **Waarschijnlijke oorzaken:**
            - Mobile Racking software draait niet
            - TCP-IP server module niet actief  
            - Verkeerde poort configuratie
            - PLC in STOP mode
            
            **Vereiste actie:**
            Neem contact op met PLC technicus om:
            1. Mobile Racking software te starten
            2. TCP-IP communicatie module te activeren
            3. Poort configuratie te verifiëren
            """)
        
        # Toon voorbeelddata
        st.header("📖 Voorbeeld WMS Data Structuur")
        
        example_data = []
        for key, field in list(WMS_DATA_STRUCTURE.items())[:10]:  # Toon eerste 10
            example_data.append({
                'Parameter': field.name[:30] + "..." if len(field.name) > 30 else field.name,
                'Type': field.data_type.value,
                'Offset': str(field.offset),
                'Start Value': str(field.start_value),
                'Comment': field.comment[:50] + "..." if len(field.comment) > 50 else field.comment
            })
        
        df = pd.DataFrame(example_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
