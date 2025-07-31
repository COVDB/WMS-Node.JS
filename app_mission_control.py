"""
STOW WMS Mobile Racking - Live Mission Control Dashboard
Complete one-pager met alle commando's, real-time monitoring en visualisaties
"""

import streamlit as st
import pandas as pd
import time
import socket
import datetime
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
import json

# Import enhanced parser
try:
    from enhanced_response_parser import (
        parse_enhanced_mobile_response, 
        get_safety_assessment, 
        decode_boolean_flags_byte5,
        decode_alarm_flags
    )
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="STOW WMS Mission Control",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS voor dashboard look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 0 0 15px 15px;
        color: white;
        text-align: center;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
        margin: 0.5rem 0;
    }
    
    .alarm-active { 
        background-color: #ffebee !important; 
        border-left: 4px solid #f44336 !important;
    }
    
    .status-ok { 
        background-color: #e8f5e8 !important; 
        border-left: 4px solid #4caf50 !important;
    }
    
    .status-warning { 
        background-color: #fff3e0 !important; 
        border-left: 4px solid #ff9800 !important;
    }
    
    .command-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
    }
    
    .gang-button {
        margin: 2px;
        min-height: 60px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'live_monitoring' not in st.session_state:
    st.session_state.live_monitoring = False
if 'status_history' not in st.session_state:
    st.session_state.status_history = []
if 'command_history' not in st.session_state:
    st.session_state.command_history = []
if 'last_status' not in st.session_state:
    st.session_state.last_status = None
if 'plc_ip' not in st.session_state:
    st.session_state.plc_ip = "1.1.1.2"
if 'plc_port' not in st.session_state:
    st.session_state.plc_port = 2000

# Header
st.markdown("""
<div class="main-header">
    <h1>🚀 STOW WMS Mission Control Dashboard</h1>
    <p>Live PLC Command & Control • Real-time Monitoring • Complete System Overview</p>
</div>
""", unsafe_allow_html=True)

def send_plc_command(command_bytes: bytes, command_description: str):
    """Send command to PLC and get response"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((st.session_state.plc_ip, st.session_state.plc_port))
        
        # Send command
        sock.send(command_bytes)
        
        # Get response
        response = sock.recv(20)
        sock.close()
        
        # Parse if possible
        parsed_status = None
        if PARSER_AVAILABLE:
            parsed_status = parse_enhanced_mobile_response(response)
        
        # Log command
        command_log = {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'command': command_description,
            'command_bytes': list(command_bytes),
            'response_bytes': list(response),
            'success': True,
            'parsed': parsed_status
        }
        
        st.session_state.command_history.append(command_log)
        if parsed_status:
            st.session_state.last_status = parsed_status
        
        return {"success": True, "response": response, "parsed": parsed_status}
        
    except Exception as e:
        error_log = {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'command': command_description,
            'command_bytes': list(command_bytes),
            'error': str(e),
            'success': False
        }
        st.session_state.command_history.append(error_log)
        return {"success": False, "error": str(e)}

def create_gang_visualization():
    """Create visual representation of gang status"""
    if not st.session_state.last_status:
        return None
    
    # Create gang status grid
    fig = go.Figure()
    
    # Grid layout for 32 gangs (8x4)
    rows, cols = 4, 8
    gang_states = st.session_state.last_status.get('aisle_lighting', {})
    
    for i in range(1, 33):
        row = (i - 1) // cols
        col = (i - 1) % cols
        
        is_lit = gang_states.get(i, False)
        color = '#4CAF50' if is_lit else '#E0E0E0'
        
        fig.add_shape(
            type="rect",
            x0=col, y0=3-row, x1=col+0.8, y1=3-row+0.8,
            fillcolor=color,
            line=dict(color='black', width=1)
        )
        
        fig.add_annotation(
            x=col+0.4, y=3-row+0.4,
            text=str(i),
            showarrow=False,
            font=dict(color='white' if is_lit else 'black', size=12, family="Arial Black")
        )
    
    fig.update_layout(
        title="Gang Verlichting Status (Real-time)",
        xaxis=dict(range=[-0.5, 8.5], showgrid=False, showticklabels=False),
        yaxis=dict(range=[-0.5, 4.5], showgrid=False, showticklabels=False),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_alarm_heatmap():
    """Create alarm status heatmap"""
    if not st.session_state.last_status or 'alarms' not in st.session_state.last_status:
        return None
    
    alarms = st.session_state.last_status['alarms']
    
    # Group alarms by category
    categories = {
        'PDS Sensors': ['pds_front_interrupted', 'pds_back_interrupted', 'pds_side_interrupted'],
        'Emergency': ['emergency_shutdown', 'emergency_button_slave'],
        'Detection': ['underdrive_sensor_detection', 'underdrive_sensor_slave', 'fds_sensor_issue'],
        'Pallet Systems': ['pallet_detection_master', 'pallet_detection_slave'],
        'Relays': ['50k1_relay_off', '50k2_relay_off'],
        'Other': ['pd_slave_not_ok']
    }
    
    # Create data for heatmap
    z_data = []
    y_labels = []
    
    for category, alarm_list in categories.items():
        for alarm in alarm_list:
            if alarm in alarms:
                z_data.append([1 if alarms[alarm] else 0])
                y_labels.append(alarm.replace('_', ' ').title())
    
    if not z_data:
        return None
    
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        y=y_labels,
        x=['Status'],
        colorscale=[[0, '#4CAF50'], [1, '#F44336']],
        showscale=False,
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Alarm Status Overzicht",
        height=400,
        margin=dict(l=150, r=20, t=40, b=20)
    )
    
    return fig

# Main dashboard layout
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("🔧 PLC Connection")
    
    # Connection settings
    with st.expander("⚙️ Settings", expanded=False):
        st.session_state.plc_ip = st.text_input("PLC IP", value=st.session_state.plc_ip)
        st.session_state.plc_port = st.number_input("PLC Port", value=st.session_state.plc_port, min_value=1, max_value=65535)
    
    # Live monitoring toggle
    st.session_state.live_monitoring = st.toggle("🔴 Live Monitoring", value=st.session_state.live_monitoring)
    
    # Manual status request
    if st.button("📊 STATUS REQUEST", type="primary"):
        with st.spinner("Status opvragen..."):
            result = send_plc_command(bytes([0, 2]), "Status Request")
            if result["success"]:
                st.success("✅ Status ontvangen!")
            else:
                st.error(f"❌ Fout: {result['error']}")
    
    # Current system status
    if st.session_state.last_status:
        st.subheader("📈 System Status")
        
        if PARSER_AVAILABLE:
            safety_color, safety_status, safety_advice = get_safety_assessment(st.session_state.last_status)
            
            if "🟢" in safety_color:
                st.success(f"{safety_color} {safety_status}")
            elif "🟡" in safety_color:
                st.warning(f"{safety_color} {safety_status}")
            else:
                st.error(f"{safety_color} {safety_status}")
            
            st.caption(safety_advice)
            
            # Quick metrics
            ops = st.session_state.last_status.get('operating_flags', {})
            st.metric("Software", st.session_state.last_status.get('software_version', 'N/A'))
            st.metric("Power", "🟢 ON" if ops.get('power_on', False) else "🔴 OFF")
            st.metric("Mode", "AUTO" if ops.get('auto_mode_active', False) else "MANUAL")

with col2:
    st.subheader("🎮 Command Center")
    
    # Command tabs
    cmd_tab1, cmd_tab2, cmd_tab3 = st.tabs(["🚪 Gang Commands", "⚙️ System Commands", "🔧 Advanced"])
    
    with cmd_tab1:
        st.write("**Gang Besturing (1-32)**")
        
        # Gang command options
        col1a, col1b = st.columns(2)
        with col1a:
            protocol_type = st.selectbox("Protocol", ["Simple [gang, 1]", "Legacy WMS"], key="gang_protocol")
        with col1b:
            gang_range = st.selectbox("Gang Range", ["1-8", "9-16", "17-24", "25-32"], key="gang_range")
        
        # Determine gang range
        range_map = {"1-8": (1, 9), "9-16": (9, 17), "17-24": (17, 25), "25-32": (25, 33)}
        start_gang, end_gang = range_map[gang_range]
        
        # Gang buttons
        gang_cols = st.columns(4)
        for i in range(start_gang, end_gang):
            col_idx = (i - start_gang) % 4
            with gang_cols[col_idx]:
                if st.button(f"Gang {i}", key=f"gang_btn_{i}"):
                    if protocol_type == "Simple [gang, 1]":
                        cmd_bytes = bytes([i, 1])
                    else:
                        # Legacy WMS protocol
                        start_byte = 0x02
                        length = 2
                        command = 0x4F
                        aisle_byte = i
                        checksum = length ^ command ^ aisle_byte
                        end_byte = 0x03
                        cmd_bytes = bytes([start_byte, length, command, aisle_byte, checksum, end_byte])
                    
                    with st.spinner(f"Gang {i} openen..."):
                        result = send_plc_command(cmd_bytes, f"Open Gang {i}")
                        if result["success"]:
                            st.success(f"✅ Gang {i} commando verzonden!")
                        else:
                            st.error(f"❌ Gang {i} fout: {result['error']}")
    
    with cmd_tab2:
        st.write("**Systeem Commando's**")
        
        sys_col1, sys_col2 = st.columns(2)
        
        with sys_col1:
            if st.button("🔄 System Reset", type="secondary"):
                # Custom reset command (implementation depends on PLC)
                result = send_plc_command(bytes([255, 0]), "System Reset")
                if result["success"]:
                    st.success("✅ Reset commando verzonden!")
                else:
                    st.error(f"❌ Reset fout: {result['error']}")
            
            if st.button("🚨 Emergency Stop", type="secondary"):
                # Emergency stop command
                result = send_plc_command(bytes([0, 255]), "Emergency Stop")
                if result["success"]:
                    st.warning("⚠️ Emergency stop verzonden!")
                else:
                    st.error(f"❌ Emergency stop fout: {result['error']}")
        
        with sys_col2:
            if st.button("💡 All Lights ON", type="secondary"):
                result = send_plc_command(bytes([100, 1]), "All Lights ON")
                if result["success"]:
                    st.success("✅ Alle lichten aan!")
                else:
                    st.error(f"❌ Lichten fout: {result['error']}")
            
            if st.button("🌙 All Lights OFF", type="secondary"):
                result = send_plc_command(bytes([100, 0]), "All Lights OFF")
                if result["success"]:
                    st.success("✅ Alle lichten uit!")
                else:
                    st.error(f"❌ Lichten fout: {result['error']}")
    
    with cmd_tab3:
        st.write("**Custom Command**")
        
        # Custom command builder
        custom_col1, custom_col2 = st.columns(2)
        
        with custom_col1:
            byte1 = st.number_input("Byte 1", min_value=0, max_value=255, value=0, key="custom_byte1")
            byte2 = st.number_input("Byte 2", min_value=0, max_value=255, value=2, key="custom_byte2")
        
        with custom_col2:
            custom_description = st.text_input("Command Description", value="Custom Command", key="custom_desc")
            
            if st.button("📤 Send Custom Command", type="primary"):
                cmd_bytes = bytes([byte1, byte2])
                result = send_plc_command(cmd_bytes, custom_description)
                if result["success"]:
                    st.success(f"✅ {custom_description} verzonden!")
                else:
                    st.error(f"❌ Fout: {result['error']}")

with col3:
    st.subheader("📊 Live Data")
    
    # Response data display
    if st.session_state.last_status:
        with st.container():
            st.write("**Laatste Response:**")
            st.code(f"Raw: {st.session_state.last_status.get('raw_response', [])}")
            st.code(f"Hex: {st.session_state.last_status.get('hex_response', 'N/A')}")
            st.caption(f"Tijd: {st.session_state.last_status.get('timestamp', 'N/A')}")
    
    # Command history
    st.subheader("📝 Command Log")
    if st.session_state.command_history:
        # Show last 5 commands
        recent_commands = st.session_state.command_history[-5:]
        for cmd in reversed(recent_commands):
            success_emoji = "✅" if cmd.get('success', False) else "❌"
            st.write(f"{success_emoji} **{cmd['timestamp']}** - {cmd['command']}")
            if not cmd.get('success', False):
                st.caption(f"Error: {cmd.get('error', 'Unknown')}")
    else:
        st.info("Geen commando's verzonden")
    
    # Clear history button
    if st.button("🗑️ Clear History"):
        st.session_state.command_history = []
        st.rerun()

# Visualizations section
if st.session_state.last_status:
    st.subheader("📈 Live Visualizations")
    
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        # Gang lighting visualization
        gang_fig = create_gang_visualization()
        if gang_fig:
            st.plotly_chart(gang_fig, use_container_width=True)
    
    with viz_col2:
        # Alarm heatmap
        alarm_fig = create_alarm_heatmap()
        if alarm_fig:
            st.plotly_chart(alarm_fig, use_container_width=True)

# Live monitoring auto-refresh
if st.session_state.live_monitoring:
    st.info("🔴 Live monitoring actief - Auto-refresh elke 5 seconden")
    time.sleep(5)
    # Send status request automatically
    result = send_plc_command(bytes([0, 2]), "Auto Status Request")
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 10px;'>
    <p><strong>STOW WMS Mission Control Dashboard</strong> | Live PLC Command & Control System</p>
    <p>Real-time Monitoring • Complete Command Interface • Advanced Visualizations</p>
</div>
""", unsafe_allow_html=True)
