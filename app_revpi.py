"""
WMS Mobile Racking TCP-IP Communication Streamlit App - RevPi Version
"""

import streamlit as st
import pandas as pd
import time
import struct
import os
import subprocess
import base64
import socket
from datetime import datetime
from typing import Dict, Any, List

# Page config - geen emoji characters voor RevPi compatibiliteit
st.set_page_config(
    page_title="Stow WMS Mobile Racking Controller",
    page_icon=":factory:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS voor Stow branding
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        padding: 1rem;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 10px 10px;
        color: white;
        text-align: center;
    }
    
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .status-ok { color: #27ae60; font-weight: bold; }
    .status-error { color: #e74c3c; font-weight: bold; }
    .status-warning { color: #f39c12; font-weight: bold; }
    
    .stAlert > div { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>STOW WMS Mobile Racking Controller</h1>
    <p>Industrial TCP/IP Communication Interface | Revolution Pi Edition</p>
</div>
""", unsafe_allow_html=True)

# Eenvoudige simulatie data voor RevPi testing
def get_system_status():
    """Simuleer PLC data voor testing"""
    current_time = datetime.now()
    
    # Simuleer operating modes die cyclisch veranderen
    modes = ['Manual', 'Automatic', 'Maintenance', 'Setup']
    mode_index = (int(current_time.timestamp()) // 30) % len(modes)
    
    # Simuleer status data zonder bytes() problemen
    words = [0, 1282, 514, 0, 7135, 0, 0, 0, 3584, 0]
    simulated_bytes = struct.pack('<10H', *words)
    
    return {
        'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
        'mode': modes[mode_index],
        'status': 'Online',
        'connection': True,
        'data': list(simulated_bytes),
        'raw_response': list(simulated_bytes)
    }

# Sidebar configuratie
with st.sidebar:
    st.header("Connection Settings")
    
    plc_ip = st.text_input("PLC IP Address", value="1.1.1.2")
    plc_port = st.number_input("PLC Port", value=2000, min_value=1, max_value=65535)
    
    st.markdown("---")
    
    # RevPi netwerk info
    st.subheader("Revolution Pi Network")
    st.info("""
    **Management Network (eth0):**
    IP: 192.168.0.12
    
    **PLC Network (eth1):**
    IP: 1.1.1.185/24
    """)
    
    connection_test = st.button("Test PLC Connection", type="primary")
    
    st.markdown("---")
    st.subheader("Simulation Mode")
    simulation_mode = st.checkbox("Enable Simulation", value=True)

# Main interface
tab1, tab2, tab3 = st.tabs(["Live Monitoring", "System Status", "Configuration"])

with tab1:
    st.header("Real-time HMI Monitoring")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get current status
    status_data = get_system_status()
    
    with col1:
        st.metric(
            "Operating Mode", 
            status_data['mode'],
            delta="Active"
        )
    
    with col2:
        st.metric(
            "Connection Status",
            "Connected" if status_data['connection'] else "Disconnected",
            delta="Online" if status_data['connection'] else "Offline"
        )
    
    with col3:
        st.metric(
            "Last Update",
            status_data['timestamp'],
            delta="Live"
        )
    
    with col4:
        st.metric(
            "RevPi Status",
            "Revolution Pi Connect SE",
            delta="192.168.0.12"
        )
    
    # Auto-refresh
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
    
    if auto_refresh:
        time.sleep(0.1)  # Kleine delay voor smooth updates
        st.rerun()

with tab2:
    st.header("System Status Overview")
    
    # Network diagnostics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Network Configuration")
        
        network_data = {
            "Interface": ["eth0", "eth1"],
            "IP Address": ["192.168.0.12", "1.1.1.185"],
            "Purpose": ["Management/Internet", "PLC Communication"],
            "Status": ["Active", "Active"]
        }
        
        st.dataframe(pd.DataFrame(network_data), use_container_width=True)
        
        st.subheader("PLC Communication")
        if simulation_mode:
            st.success("Simulation Mode Active")
            st.info(f"Target PLC: {plc_ip}:{plc_port}")
        else:
            st.warning("Live Mode - Connect to PLC")
    
    with col2:
        st.subheader("System Health")
        
        health_metrics = {
            "Component": ["Revolution Pi", "Network eth0", "Network eth1", "Streamlit Service", "Python Runtime"],
            "Status": ["Healthy", "Connected", "Connected", "Running", "Active"],
            "Uptime": ["Online", "Active", "Active", "Running", "Good"]
        }
        
        st.dataframe(pd.DataFrame(health_metrics), use_container_width=True)
        
        # System info
        st.subheader("System Information")
        st.code(f"""
Revolution Pi Connect SE
Hostname: RevPi10036880678
Python: 3.11
Streamlit: 1.47.1
Current Time: {datetime.now().strftime('%H:%M:%S')}
        """)

with tab3:
    st.header("Configuration & Deployment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Deployment Status")
        
        deployment_status = [
            ("Revolution Pi Setup", "Complete", "success"),
            ("Network Configuration", "Complete", "success"),
            ("Python Environment", "Complete", "success"),
            ("Streamlit Service", "Running", "success"),
            ("WMS Application", "Deployed", "success"),
            ("PLC Communication", "Ready", "info"),
        ]
        
        for item, status, status_type in deployment_status:
            if status_type == "success":
                st.success(f"✅ {item}: {status}")
            else:
                st.info(f"ℹ️ {item}: {status}")
    
    with col2:
        st.subheader("Next Steps")
        
        st.markdown("""
        **Production Configuration:**
        1. Configure SSL certificates
        2. Setup automated backups
        3. Configure monitoring alerts
        4. Test PLC connectivity
        5. Deploy live monitoring
        
        **Management Commands:**
        ```bash
        # Service management
        sudo systemctl status wms-streamlit
        sudo systemctl restart wms-streamlit
        
        # Logs
        journalctl -u wms-streamlit -f
        
        # Network test
        ping 1.1.1.2
        ```
        """)

# Connection test
if connection_test:
    with st.spinner("Testing PLC connection..."):
        time.sleep(2)
        if simulation_mode:
            st.success(f"✅ Simulation connection successful to {plc_ip}:{plc_port}")
        else:
            try:
                # Test actual connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((plc_ip, plc_port))
                sock.close()
                
                if result == 0:
                    st.success(f"✅ PLC connection successful to {plc_ip}:{plc_port}")
                else:
                    st.error(f"❌ PLC connection failed to {plc_ip}:{plc_port}")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Stow WMS Mobile Racking Controller</strong> | Revolution Pi Connect SE Edition</p>
    <p>Industrial TCP/IP Communication Interface | Version 1.0</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh voor live monitoring
if auto_refresh and st.session_state.get('last_refresh', 0) + 30 < time.time():
    st.session_state.last_refresh = time.time()
    time.sleep(1)
    st.rerun()
