"""
STOW WMS Mobile Racking - Live Mission Control Dashboard (LOCAL VERSION)
Met simulatie mode voor lokale development en testing
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
import random

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
    page_title="STOW WMS Mission Control (LOCAL)",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS voor gaming/mission control look
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 0 0 20px 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    .metric-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .alarm-active { 
        background: linear-gradient(145deg, #ffebee 0%, #ffcdd2 100%) !important; 
        border: 2px solid #f44336 !important;
        animation: pulse 2s infinite;
    }
    
    .status-ok { 
        background: linear-gradient(145deg, #e8f5e8 0%, #c8e6c9 100%) !important; 
        border: 2px solid #4caf50 !important;
    }
    
    .status-warning { 
        background: linear-gradient(145deg, #fff3e0 0%, #ffe0b2 100%) !important; 
        border: 2px solid #ff9800 !important;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .command-section {
        background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    .gang-button {
        margin: 3px;
        min-height: 50px;
    }
    
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #ff4444;
        border-radius: 50%;
        animation: blink 1s infinite;
        margin-right: 8px;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    
    .success-glow {
        box-shadow: 0 0 20px rgba(76, 175, 80, 0.5) !important;
    }
    
    .error-glow {
        box-shadow: 0 0 20px rgba(244, 67, 54, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'live_monitoring' not in st.session_state:
    st.session_state.live_monitoring = False
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = True
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
if 'gang_states' not in st.session_state:
    st.session_state.gang_states = {i: False for i in range(1, 33)}
if 'alarm_states' not in st.session_state:
    st.session_state.alarm_states = {}

# Header
st.markdown("""
<div class="main-header">
    <h1>🎮 STOW WMS Mission Control Dashboard</h1>
    <p><span class="live-indicator"></span>Live PLC Command & Control • Real-time Monitoring • Complete System Overview</p>
</div>
""", unsafe_allow_html=True)

def simulate_plc_response(command_bytes: bytes, command_description: str):
    """Simulate PLC response for local testing"""
    
    # Base response with some randomization
    base_response = [0, 2, 2, 5, 9, 9, 0, 0, 223, 27, 0, 0, 0, 0, 0, 0, 0, 14, 0, 0]
    
    # Modify response based on command
    if len(command_bytes) >= 2:
        if command_bytes[0] == 0 and command_bytes[1] == 2:
            # Status request - return current simulated state
            pass
        elif command_bytes[1] == 1 and 1 <= command_bytes[0] <= 32:
            # Gang opening command - simulate lighting change
            gang_num = command_bytes[0]
            st.session_state.gang_states[gang_num] = True
            
            # Simulate some lighting bytes change
            if gang_num <= 8:
                base_response[10] |= (1 << (gang_num - 1))
            elif gang_num <= 16:
                base_response[11] |= (1 << (gang_num - 9))
            elif gang_num <= 24:
                base_response[12] |= (1 << (gang_num - 17))
            else:
                base_response[13] |= (1 << (gang_num - 25))
    
    # Add some random variations
    base_response[8] = random.randint(200, 255)  # Mobile data variation
    base_response[9] = random.randint(20, 30)    # More variation
    
    return bytes(base_response)

def send_plc_command(command_bytes: bytes, command_description: str):
    """Send command to PLC (real or simulated)"""
    
    if st.session_state.simulation_mode:
        # Simulate response
        time.sleep(0.1)  # Simulate network delay
        response = simulate_plc_response(command_bytes, command_description)
        
        # Randomly simulate some connection errors
        if random.random() < 0.05:  # 5% chance of error
            error_log = {
                'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                'command': command_description + " (SIMULATED)",
                'command_bytes': list(command_bytes),
                'error': "Simulated connection timeout",
                'success': False
            }
            st.session_state.command_history.append(error_log)
            return {"success": False, "error": "Simulated connection timeout"}
        
        success = True
        
    else:
        # Real PLC communication
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((st.session_state.plc_ip, st.session_state.plc_port))
            
            sock.send(command_bytes)
            response = sock.recv(20)
            sock.close()
            success = True
            
        except Exception as e:
            error_log = {
                'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                'command': command_description,
                'command_bytes': list(command_bytes),
                'error': str(e),
                'success': False
            }
            st.session_state.command_history.append(error_log)
            return {"success": False, "error": str(e)}
    
    # Parse response if available
    parsed_status = None
    if PARSER_AVAILABLE:
        try:
            parsed_status = parse_enhanced_mobile_response(response)
        except Exception as e:
            st.warning(f"Parser error: {e}")
    
    # Log successful command
    command_log = {
        'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
        'command': command_description + (" (SIMULATED)" if st.session_state.simulation_mode else ""),
        'command_bytes': list(command_bytes),
        'response_bytes': list(response),
        'response_hex': response.hex().upper(),
        'success': True,
        'parsed': parsed_status
    }
    
    st.session_state.command_history.append(command_log)
    if parsed_status:
        st.session_state.last_status = parsed_status
        # Update status history for trending
        st.session_state.status_history.append({
            'timestamp': datetime.now(),
            'status': parsed_status
        })
        # Keep only last 50 status updates
        if len(st.session_state.status_history) > 50:
            st.session_state.status_history.pop(0)
    
    return {"success": True, "response": response, "parsed": parsed_status}

def create_enhanced_gang_visualization():
    """Create enhanced gang visualization with animations"""
    if not st.session_state.last_status:
        # Use simulated states if no real data
        gang_states = st.session_state.gang_states
    else:
        gang_states = st.session_state.last_status.get('aisle_lighting', {})
    
    fig = go.Figure()
    
    # Create 3D-like gang grid
    rows, cols = 4, 8
    
    for i in range(1, 33):
        row = (i - 1) // cols
        col = (i - 1) % cols
        
        is_lit = gang_states.get(i, False)
        
        # Color scheme based on status
        if is_lit:
            color = '#00E676'  # Bright green for active
            border_color = '#4CAF50'
            text_color = 'white'
        else:
            color = '#37474F'  # Dark gray for inactive  
            border_color = '#607D8B'
            text_color = '#B0BEC5'
        
        # Main rectangle
        fig.add_shape(
            type="rect",
            x0=col*1.2, y0=(3-row)*1.2, x1=col*1.2+1, y1=(3-row)*1.2+1,
            fillcolor=color,
            line=dict(color=border_color, width=2)
        )
        
        # Add glow effect for active gangs
        if is_lit:
            fig.add_shape(
                type="rect",
                x0=col*1.2-0.1, y0=(3-row)*1.2-0.1, x1=col*1.2+1.1, y1=(3-row)*1.2+1.1,
                fillcolor='rgba(0, 230, 118, 0.3)',
                line=dict(color='rgba(0, 230, 118, 0.5)', width=1)
            )
        
        # Gang number
        fig.add_annotation(
            x=col*1.2+0.5, y=(3-row)*1.2+0.5,
            text=f"<b>{i}</b>",
            showarrow=False,
            font=dict(color=text_color, size=14, family="Arial Black")
        )
    
    fig.update_layout(
        title=dict(
            text="🏭 Gang Status Grid - Real-time Monitoring",
            font=dict(size=16, color='#1a1a1a')
        ),
        xaxis=dict(range=[-0.5, 9.5], showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(range=[-0.5, 5], showgrid=False, showticklabels=False, zeroline=False),
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white'
    )
    
    return fig

def create_status_trend_chart():
    """Create trending chart of system metrics"""
    if len(st.session_state.status_history) < 2:
        return None
    
    # Extract trending data
    timestamps = []
    software_versions = []
    tcp_status = []
    power_status = []
    
    for entry in st.session_state.status_history[-20:]:  # Last 20 entries
        timestamps.append(entry['timestamp'])
        status = entry['status']
        
        # Extract key metrics
        software_versions.append(float(status.get('software_version', '0.0').replace('.', '')))
        
        ops = status.get('operating_flags', {})
        tcp_status.append(1 if ops.get('tcp_connection_ok', False) else 0)
        power_status.append(1 if ops.get('power_on', False) else 0)
    
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=timestamps, y=tcp_status,
        mode='lines+markers',
        name='TCP Connection',
        line=dict(color='#2196F3', width=3),
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=timestamps, y=power_status,
        mode='lines+markers', 
        name='Power Status',
        line=dict(color='#4CAF50', width=3)
    ))
    
    fig.update_layout(
        title="📈 System Status Trend (Real-time)",
        xaxis_title="Time",
        yaxis_title="Status (0=OFF, 1=ON)",
        height=250,
        margin=dict(l=40, r=20, t=40, b=40),
        showlegend=True,
        legend=dict(x=0, y=1)
    )
    
    return fig

def create_command_frequency_chart():
    """Create chart showing command frequency"""
    if not st.session_state.command_history:
        return None
    
    # Count command types
    command_counts = {}
    for cmd in st.session_state.command_history[-50:]:  # Last 50 commands
        cmd_type = cmd['command'].split(' ')[0]
        command_counts[cmd_type] = command_counts.get(cmd_type, 0) + 1
    
    if not command_counts:
        return None
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=list(command_counts.keys()),
            y=list(command_counts.values()),
            marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        )
    ])
    
    fig.update_layout(
        title="📊 Command Frequency Analysis",
        xaxis_title="Command Type",
        yaxis_title="Count",
        height=250,
        margin=dict(l=40, r=20, t=40, b=40)
    )
    
    return fig

# Main dashboard layout
header_col1, header_col2, header_col3 = st.columns([2, 1, 1])

with header_col1:
    st.subheader("🔧 Mission Control Settings")

with header_col2:
    st.session_state.simulation_mode = st.toggle("🎮 Simulation Mode", value=st.session_state.simulation_mode)
    if st.session_state.simulation_mode:
        st.caption("🎯 Safe testing mode active")
    else:
        st.caption("⚡ Live PLC mode active")

with header_col3:
    st.session_state.live_monitoring = st.toggle("🔴 Live Monitoring", value=st.session_state.live_monitoring)
    if st.session_state.live_monitoring:
        st.caption("📡 Auto-refresh every 3s")

# Connection and system status row
status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    with st.container():
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not st.session_state.simulation_mode:
            conn_text = f"📡 {st.session_state.plc_ip}:{st.session_state.plc_port}"
        else:
            conn_text = "🎮 Simulation Active"
        st.metric("Connection", conn_text)
        st.markdown('</div>', unsafe_allow_html=True)

with status_col2:
    if st.button("📊 STATUS REQUEST", type="primary", use_container_width=True):
        with st.spinner("Status opvragen..."):
            result = send_plc_command(bytes([0, 2]), "Status Request")
            if result["success"]:
                st.success("✅ Status ontvangen!", icon="✅")
            else:
                st.error(f"❌ Fout: {result['error']}", icon="❌")

with status_col3:
    if st.session_state.last_status and PARSER_AVAILABLE:
        safety_color, safety_status, _ = get_safety_assessment(st.session_state.last_status)
        st.metric("System Status", f"{safety_color} {safety_status}")
    else:
        st.metric("System Status", "⚫ Unknown")

with status_col4:
    if st.session_state.last_status:
        sw_version = st.session_state.last_status.get('software_version', 'N/A')
        st.metric("Software", f"v{sw_version}")
    else:
        st.metric("Software", "Unknown")

st.markdown("---")

# Main control interface
control_col1, control_col2 = st.columns([3, 2])

with control_col1:
    st.subheader("🎮 Command Center")
    
    # Gang control section
    st.markdown('<div class="command-section">', unsafe_allow_html=True)
    st.write("**🚪 Gang Commands (Quick Access)**")
    
    gang_range_col1, gang_range_col2, gang_range_col3 = st.columns(3)
    
    with gang_range_col1:
        st.write("**Gangen 1-8:**")
        for i in range(1, 9):
            if st.button(f"Gang {i}", key=f"gang_quick_{i}", use_container_width=True):
                result = send_plc_command(bytes([i, 1]), f"Open Gang {i}")
                if result["success"]:
                    st.success(f"✅ Gang {i} opened!")
                else:
                    st.error(f"❌ Gang {i} error!")
    
    with gang_range_col2:
        st.write("**Gangen 9-16:**")
        for i in range(9, 17):
            if st.button(f"Gang {i}", key=f"gang_quick_{i}", use_container_width=True):
                result = send_plc_command(bytes([i, 1]), f"Open Gang {i}")
                if result["success"]:
                    st.success(f"✅ Gang {i} opened!")
                else:
                    st.error(f"❌ Gang {i} error!")
    
    with gang_range_col3:
        st.write("**Gangen 17-24:**")
        for i in range(17, 25):
            if st.button(f"Gang {i}", key=f"gang_quick_{i}", use_container_width=True):
                result = send_plc_command(bytes([i, 1]), f"Open Gang {i}")
                if result["success"]:
                    st.success(f"✅ Gang {i} opened!")
                else:
                    st.error(f"❌ Gang {i} error!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # System commands
    st.markdown('<div class="command-section">', unsafe_allow_html=True)
    st.write("**⚙️ System Commands**")
    
    sys_cmd_col1, sys_cmd_col2, sys_cmd_col3, sys_cmd_col4 = st.columns(4)
    
    with sys_cmd_col1:
        if st.button("🔄 Reset", use_container_width=True):
            result = send_plc_command(bytes([255, 0]), "System Reset")
            if result["success"]:
                st.success("Reset sent!")
    
    with sys_cmd_col2:
        if st.button("💡 Lights ON", use_container_width=True):
            result = send_plc_command(bytes([100, 1]), "All Lights ON")
            if result["success"]:
                st.success("Lights ON!")
    
    with sys_cmd_col3:
        if st.button("🌙 Lights OFF", use_container_width=True):
            result = send_plc_command(bytes([100, 0]), "All Lights OFF")
            if result["success"]:
                st.success("Lights OFF!")
    
    with sys_cmd_col4:
        if st.button("🚨 E-Stop", use_container_width=True):
            result = send_plc_command(bytes([0, 255]), "Emergency Stop")
            if result["success"]:
                st.warning("E-Stop sent!")
    
    st.markdown('</div>', unsafe_allow_html=True)

with control_col2:
    st.subheader("📊 Live Data Monitor")
    
    # Current status display
    if st.session_state.last_status:
        with st.container():
            st.markdown('<div class="metric-card status-ok">', unsafe_allow_html=True)
            st.write("**📡 Latest Response:**")
            
            # Key metrics
            if PARSER_AVAILABLE:
                ops = st.session_state.last_status.get('operating_flags', {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Power:** {'🟢 ON' if ops.get('power_on', False) else '🔴 OFF'}")
                    st.write(f"**TCP:** {'🟢 OK' if ops.get('tcp_connection_ok', False) else '🔴 ERR'}")
                
                with col2:
                    st.write(f"**Mode:** {'AUTO' if ops.get('auto_mode_active', False) else 'MANUAL'}")
                    st.write(f"**Released:** {'🟢 YES' if ops.get('installation_released', False) else '🔴 NO'}")
            
            # Raw data
            raw_data = st.session_state.last_status.get('raw_response', [])
            if raw_data:
                st.text(f"Raw: {raw_data[:10]}...")
                st.text(f"Hex: {st.session_state.last_status.get('hex_response', 'N/A')[:20]}...")
            
            st.caption(f"Updated: {st.session_state.last_status.get('timestamp', 'Unknown')}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Command history
    st.write("**📝 Recent Commands:**")
    if st.session_state.command_history:
        recent_commands = st.session_state.command_history[-8:]
        for cmd in reversed(recent_commands):
            success_emoji = "✅" if cmd.get('success', False) else "❌"
            timestamp = cmd['timestamp']
            command = cmd['command'][:25] + "..." if len(cmd['command']) > 25 else cmd['command']
            st.write(f"{success_emoji} `{timestamp}` {command}")
    else:
        st.info("No commands sent yet")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.command_history = []
        st.rerun()

# Visualizations section
st.subheader("📈 Live System Visualizations")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    gang_fig = create_enhanced_gang_visualization()
    if gang_fig:
        st.plotly_chart(gang_fig, use_container_width=True)

with viz_col2:
    trend_fig = create_status_trend_chart()
    if trend_fig:
        st.plotly_chart(trend_fig, use_container_width=True)
    else:
        st.info("📊 Waiting for more data to show trends...")

# Additional analytics
analytics_col1, analytics_col2 = st.columns(2)

with analytics_col1:
    freq_fig = create_command_frequency_chart()
    if freq_fig:
        st.plotly_chart(freq_fig, use_container_width=True)

with analytics_col2:
    if st.session_state.last_status and PARSER_AVAILABLE and 'alarms' in st.session_state.last_status:
        st.write("**🚨 Active Alarms:**")
        alarms = st.session_state.last_status['alarms']
        active_alarms = [alarm for alarm, active in alarms.items() if active]
        
        if active_alarms:
            for alarm in active_alarms[:8]:  # Show max 8
                st.error(f"🚨 {alarm.replace('_', ' ').title()}")
        else:
            st.success("✅ No active alarms")

# Live monitoring auto-refresh
if st.session_state.live_monitoring:
    # Show pulsing indicator
    st.markdown("""
    <div style='position: fixed; top: 70px; right: 20px; background: rgba(255,0,0,0.8); 
                color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;'>
        <span class="live-indicator"></span>LIVE
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(3)  # 3 second refresh
    # Send automatic status request
    result = send_plc_command(bytes([0, 2]), "Auto Status Request")
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 15px; background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px;'>
    <p><strong>🎮 STOW WMS Mission Control Dashboard</strong> | Advanced PLC Command & Control System</p>
    <p>Real-time Monitoring • Interactive Commands • Live Visualizations • Local Development Ready</p>
</div>
""", unsafe_allow_html=True)
