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
    
    try:
        if st.session_state.client:
            st.session_state.client.disconnect()
        
        st.session_state.client = TCPClient(host, port)
        success = st.session_state.client.connect()
        st.session_state.connected = success
        
        if success:
            st.success(f"Verbonden met {host}:{port}")
            wms_logger.log_connection(host, port, True)
        else:
            st.error(f"Verbinding mislukt naar {host}:{port}")
            wms_logger.log_connection(host, port, False)
            
    except Exception as e:
        st.error(f"Fout bij verbinden: {e}")
        st.session_state.connected = False

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
    port = st.sidebar.number_input("Poort", min_value=1, max_value=65535, value=2000, key="port")
    
    # Verbinding knoppen
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Verbinden", type="primary", disabled=st.session_state.connected):
            create_connection()
    
    with col2:
        if st.button("Verbreken", disabled=not st.session_state.connected):
            disconnect()
    
    # Status indicator
    if st.session_state.connected:
        st.sidebar.success("🟢 Verbonden")
    else:
        st.sidebar.error("🔴 Niet verbonden")
    
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
                'Offset': field_info.offset if field_info else 'N/A',
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
        
        # Toon voorbeelddata
        st.header("📖 Voorbeeld WMS Data Structuur")
        
        example_data = []
        for key, field in list(WMS_DATA_STRUCTURE.items())[:10]:  # Toon eerste 10
            example_data.append({
                'Parameter': field.name[:30] + "..." if len(field.name) > 30 else field.name,
                'Type': field.data_type.value,
                'Offset': field.offset,
                'Start Value': field.start_value,
                'Comment': field.comment[:50] + "..." if len(field.comment) > 50 else field.comment
            })
        
        df = pd.DataFrame(example_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
