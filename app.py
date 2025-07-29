"""
WMS Mobile Racking TCP-IP Communication Streamlit App
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
from protocol_generators import get_available_languages, generate_protocol_code, get_file_extension

# Page config
st.set_page_config(
    page_title="Stow WMS Mobile Racking Controller",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Stow branding
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
    
    .stow-logo {
        height: 60px;
        margin-right: 20px;
        vertical-align: middle;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #2980b9 0%, #1f639a 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .status-success {
        color: #27ae60;
        font-weight: bold;
    }
    
    .status-error {
        color: #e74c3c;
        font-weight: bold;
    }
    
    .stow-orange {
        color: #ff6b35;
        font-weight: bold;
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

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
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = ""
if 'selected_language' not in st.session_state:
    st.session_state.selected_language = "Node.js"

def create_connection():
    """Create connection to Mobile Racking controller"""
    host = st.session_state.get('host', '1.1.1.2')
    port = st.session_state.get('port', 2000)
    
    # Check if running in cloud environment
    import os
    is_cloud = os.getenv('STREAMLIT_SHARING') or 'streamlit.app' in os.getenv('HOSTNAME', '')
    
    if is_cloud:
        st.warning("🌐 **Cloud Environment Detected**")
        st.info("""
        **TCP-IP connections to external systems are not available in Streamlit Community Cloud.**
        
        **For full PLC connectivity:**
        1. Download this app from GitHub
        2. Run locally: `streamlit run app.py`
        3. Connect to your Mobile Racking system
        
        **Available in Cloud:**
        - ✅ Code Generator (all languages)
        - ✅ Documentation and guides
        - ✅ Interface preview
        - ✅ Offline diagnostics
        """)
        return False
    
    # Progress bar and status updates
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("🔍 Initializing connection...")
        progress_bar.progress(10)
        
        if st.session_state.client:
            st.session_state.client.disconnect()
        
        status_text.text(f"🔌 Connecting to {host}:{port}...")
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
            st.success(f"✅ Connected to {host}:{port}")
            wms_logger.log_connection(host, port, True)
            
            # Test directly with a status request
            with st.spinner("📊 Testing connection with status request..."):
                status = st.session_state.client.get_status()
                if status:
                    st.info("🎉 Status successfully received - connection works!")
                else:
                    st.warning("⚠️ Connection OK but no status received")
        else:
            st.session_state.connected = False
            status_text.empty()
            progress_bar.empty()
            
            # Detailed error message
            st.error(f"❌ Connection failed to {host}:{port}")
            
            # Give specific diagnostic tips
            with st.expander("🔍 Diagnostics and solutions", expanded=True):
                st.markdown("""
                **Possible causes:**
                
                1. **PLC Service not active**
                   - Mobile Racking software not running
                   - TCP-IP server module not started
                   - PLC in STOP mode
                
                2. **Network problems**
                   - VPN connection unstable
                   - Firewall blocking port 2000
                   - Port forwarding not configured
                
                3. **Configuration problems**
                   - Wrong IP address
                   - Wrong port number
                   - PLC TCP-IP module misconfigured
                
                **What to do:**
                1. Check if you can ping the PLC: `ping 1.1.1.2`
                2. Check if Mobile Racking software is running on the PLC
                3. Ask PLC administrator to check TCP-IP server status
                4. Test from another machine on the same network
                """)
                
                # Test buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🏓 Test Ping"):
                        with st.spinner("Pinging..."):
                            # This could be implemented with subprocess
                            st.info("Ping test function - implement in terminal")
                
                with col2:
                    if st.button("🔍 Extended Diagnostics"):
                        st.info("Run 'python diagnose_plc.py' in terminal for full diagnostics")
            
            wms_logger.log_connection(host, port, False)
            
    except Exception as e:
        st.session_state.connected = False
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Unexpected error: {e}")
        
        with st.expander("📋 Technical details"):
            st.code(str(e))
            st.markdown("**Debug info:** Check logs for more details")

def disconnect():
    """Disconnect from controller"""
    if st.session_state.client:
        st.session_state.client.disconnect()
    st.session_state.connected = False
    st.session_state.client = None
    st.info("Connection closed")

def get_system_status():
    """Get system status"""
    if not st.session_state.connected or not st.session_state.client:
        return None
    
    try:
        status = st.session_state.client.get_status()
        if status:
            # Add timestamp
            status['timestamp'] = datetime.now()
            
            # Add to history
            st.session_state.status_history.append(status.copy())
            
            # Keep only last 100 entries
            if len(st.session_state.status_history) > 100:
                st.session_state.status_history = st.session_state.status_history[-100:]
            
            st.session_state.last_status = status
            return status
        else:
            st.error("No status received")
            return None
            
    except Exception as e:
        st.error(f"Error getting status: {e}")
        return None

def send_command(command: int):
    """Send command to controller"""
    if not st.session_state.connected or not st.session_state.client:
        st.error("No connection")
        return False
    
    try:
        response = st.session_state.client.send_command(command)
        if response:
            st.success(f"Command {command} sent")
            wms_logger.log_command(command, len(response))
            return True
        else:
            st.error(f"Command {command} failed")
            wms_logger.log_command(command, None)
            return False
            
    except Exception as e:
        st.error(f"Error sending command: {e}")
        return False

def render_sidebar():
    """Render sidebar with connection configuration"""
    with st.sidebar:
        # Stow branding in sidebar
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #3498db, #2980b9); border-radius: 10px; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0;">Stow Group</h3>
            <p style="color: #ecf0f1; margin: 0; font-size: 0.9rem;">Mobile Racking Control</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.header("🔌 Connection")
        
        # Connection configuration
        host = st.text_input("IP Address", value="1.1.1.2", key="host")
        
        # Port selection with detection
        st.write("**Port Configuration:**")
        port_option = st.radio(
            "Select port:",
            ["2001 (Detected ✅)", "2000 (Original)", "Custom"],
            key="port_option"
        )
        
        if port_option == "2001 (Detected ✅)":
            port = 2001
            st.success("Port 2001 detected as open!")
        elif port_option == "2000 (Original)":
            port = 2000
            st.warning("Port 2000 appears closed")
        else:  # Custom
            port = st.number_input("Custom port:", min_value=1, max_value=65535, value=2001)
        
        st.session_state.port = port
        
        # Connection status indicator with Stow styling
        if st.session_state.connected:
            st.markdown("""
            <div style="background: #27ae60; color: white; padding: 0.5rem; border-radius: 5px; text-align: center; margin: 1rem 0;">
                🟢 Connected to {}:{}
            </div>
            """.format(host, port), unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #e74c3c; color: white; padding: 0.5rem; border-radius: 5px; text-align: center; margin: 1rem 0;">
                🔴 Not Connected
            </div>
            """, unsafe_allow_html=True)
        
        # Connection buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Connect", type="primary", disabled=st.session_state.connected):
                create_connection()
        
        with col2:
            if st.button("Disconnect", disabled=not st.session_state.connected):
                disconnect()
        
        st.divider()
        
        # Navigation with Stow styling
        st.markdown("### 🧭 Navigation")
        selected_page = st.radio(
            "Choose section:",
            ["📊 Dashboard", "🎛️ Controls", "🔍 Diagnostics", "💻 Code Generator"],
            index=0,
            key="navigation"
        )
        
        st.divider()
        
        # Quick diagnostics
        st.header("🔍 Quick Diagnostics")
        
        if st.button("🏓 Ping Test", help="Test network connectivity"):
            with st.spinner("Testing connectivity..."):
                import subprocess
                try:
                    result = subprocess.run(['ping', host, '-n', '1'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        st.success(f"✅ {host} is reachable")
                    else:
                        st.error(f"❌ {host} is not reachable")
                except:
                    st.error("❌ Ping test failed")
        
        # Footer with Stow branding
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.8rem;">
            <p><strong>Stow Group</strong><br>
            Mobile Racking Solutions<br>
            <span class="stow-orange">Powered by Innovation</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        return selected_page
    
    if st.button("Port Scan", help="Scan open ports on the PLC"):
        with st.spinner("Scanning ports..."):
            # Quick port test for diagnostics
            from port_scanner import test_port
            test_ports = [2000, 2001, 2002, 102, 4840]
            open_ports = []
            
            for p in test_ports:
                _, is_open, response_time = test_port(host, p, 3)
                if is_open:
                    open_ports.append((p, response_time))
            
            if open_ports:
                st.sidebar.success(f"Open ports found:")
                for p, rt in open_ports:
                    st.sidebar.write(f"• Port {p} ({rt:.0f}ms)")
            else:
                st.sidebar.error("No open ports found")
    
    st.sidebar.divider()
    
    # Auto refresh
    st.sidebar.header("⚙️ Settings")
    auto_refresh = st.sidebar.checkbox(
        "Auto refresh (5s)",
        value=st.session_state.auto_refresh,
        key="auto_refresh"
    )
    
    if auto_refresh and st.session_state.connected:
        time.sleep(5)
        st.rerun()
    
    return selected_page

def render_status_overview(status: Dict[str, Any]):
    """Render status overview with Stow branding"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #3498db, #2980b9); padding: 1rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h2 style="margin: 0;">📊 Stow Mobile Racking System Status</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Real-time monitoring and control interface</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Validation
    validation = validate_status_data(status)
    
    # Alerts with Stow styling
    if validation['errors']:
        for error in validation['errors']:
            st.markdown(f"""
            <div style="background: #e74c3c; color: white; padding: 1rem; border-radius: 5px; margin: 0.5rem 0;">
                🚨 <strong>Error:</strong> {error}
            </div>
            """, unsafe_allow_html=True)
    
    if validation['warnings']:
        for warning in validation['warnings']:
            st.markdown(f"""
            <div style="background: #f39c12; color: white; padding: 1rem; border-radius: 5px; margin: 0.5rem 0;">
                ⚠️ <strong>Warning:</strong> {warning}
            </div>
            """, unsafe_allow_html=True)
    
    # Status metrics with enhanced styling
    st.markdown("### System Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        tcp_status = "🟢 Connected" if status.get('tcp_ip_connection', False) else "🔴 Disconnected"
        tcp_color = "#27ae60" if status.get('tcp_ip_connection', False) else "#e74c3c"
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: {tcp_color};">TCP-IP Connection</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">{tcp_status}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        power_status = "🟢 Online" if status.get('power_on', False) else "🔴 Offline"
        power_color = "#27ae60" if status.get('power_on', False) else "#e74c3c"
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: {power_color};">System Power</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">{power_status}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        mode = "Automatic" if status.get('automatic_mode_on', False) else "Manual"
        mode_color = "#3498db" if status.get('automatic_mode_on', False) else "#f39c12"
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: {mode_color};">Operation Mode</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">{mode}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        mobile_qty = status.get('mobile_quantity', 0)
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: #8e44ad;">Mobile Units</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">{mobile_qty} Active</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional metrics
    st.markdown("### Position & Status Details")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pos1 = status.get('position_1', 0) / 100.0
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: #16a085;">Position 1</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">{pos1:.2f}m</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        pos2 = status.get('position_2', 0) / 100.0
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: #16a085;">Position 2</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">{pos2:.2f}m</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        lighting = "🟢 On" if status.get('lighting_on', False) else "🔴 Off"
        lighting_color = "#f39c12" if status.get('lighting_on', False) else "#95a5a6"
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0; color: {lighting_color};">Lighting System</h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: bold;">{lighting}</p>
        </div>
        """, unsafe_allow_html=True)

def render_detailed_status(status: Dict[str, Any]):
    """Render detailed status table"""
    st.header("📋 Detailed Status")
    
    # Create DataFrame
    status_data = []
    descriptions = get_status_description(status)
    
    for key, value in status.items():
        if key != 'timestamp':
            field_info = WMS_DATA_STRUCTURE.get(key)
            status_data.append({
                'Parameter': key.replace('_', ' ').title(),
                'Value': descriptions.get(key, str(value)),
                'Type': field_info.data_type.value if field_info else 'Unknown',
                'Offset': str(field_info.offset) if field_info else 'N/A',
                'Description': field_info.comment if field_info else 'N/A'
            })
    
    df = pd.DataFrame(status_data)
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("Filter by type:", ["All", "Bool", "Byte", "DWord"])
    with col2:
        show_only_active = st.checkbox("Only active values")
    
    # Apply filters
    if filter_type != "All":
        df = df[df['Type'] == filter_type]
    
    if show_only_active:
        df = df[df['Value'].isin(['OK', 'True']) | df['Value'].str.isdigit()]
    
    # Display table
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_lighting_control(status: Dict[str, Any]):
    """Render lighting control interface"""
    st.header("💡 Lighting Control")
    
    # Parse current lighting rules
    lighting_rules = status.get('lighting_rules', 0)
    active_aisles = parse_lighting_rules(lighting_rules)
    
    st.write(f"Active aisles: {', '.join(map(str, active_aisles)) if active_aisles else 'None'}")
    
    # Aisle selection (1-32)
    col1, col2 = st.columns(2)
    
    with col1:
        selected_aisles = st.multiselect(
            "Select aisles to activate:",
            options=list(range(1, 33)),
            default=active_aisles,
            key="lighting_aisles"
        )
    
    with col2:
        if st.button("Update Lighting", type="primary"):
            # This would require a custom command implementation
            st.info("Lighting update functionality not yet implemented")

def render_command_interface():
    """Render command interface"""
    st.header("🎛️ Command Interface")
    
    # Predefined commands
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Basic Commands")
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
            "Command number (0-65535):",
            min_value=0,
            max_value=65535,
            value=0
        )
    
    with col2:
        if st.button("Send"):
            send_command(custom_command)

def render_history_chart():
    """Render status history chart"""
    st.header("📈 Status History")
    
    if not st.session_state.status_history:
        st.info("No history data available")
        return
    
    # Create DataFrame from history
    history_df = pd.DataFrame(st.session_state.status_history)
    
    # Select parameters to plot
    numeric_params = [
        'mobile_quantity', 'counter_lift_track_inside', 
        'stow_mobile_racking_major', 'stow_mobile_racking_minor'
    ]
    
    selected_param = st.selectbox(
        "Select parameter:",
        options=numeric_params,
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_param in history_df.columns:
        fig = px.line(
            history_df,
            x='timestamp',
            y=selected_param,
            title=f"{selected_param.replace('_', ' ').title()} over time"
        )
        st.plotly_chart(fig, use_container_width=True)

# This duplicate main function has been removed - keeping only the final main function with Stow branding

def render_protocol_generator():
    """Render multi-language protocol code generator with Stow branding"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #3498db, #2980b9); padding: 1rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
        <h2 style="margin: 0;">💻 Stow Multi-Language Protocol Generator</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Generate TCP-IP communication code for various programming languages</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    Generate professional TCP-IP communication code in various programming languages.
    This allows you to integrate the **Stow WMS Mobile Racking system** into different platforms and development environments.
    """)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Configuration section with Stow styling
        st.markdown("""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #3498db;">
            <h3 style="margin: 0; color: #2c3e50;">🔧 Configuration</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Spacing
        
        # Language selection
        languages = get_available_languages()
        selected_language = st.selectbox(
            "Programming Language",
            languages,
            index=languages.index(st.session_state.selected_language),
            key="language_selector"
        )
        st.session_state.selected_language = selected_language
        
        # Host and port
        host = st.text_input("Host IP", value="1.1.1.2")
        port = st.number_input("Port", value=2001, min_value=1, max_value=65535)
        
        # Code type selection
        code_type = st.selectbox(
            "Code Type",
            ["complete", "connection", "command", "parsing"],
            format_func=lambda x: {
                "complete": "Complete Example",
                "connection": "Connection Only",
                "command": "Send Command",
                "parsing": "Parse Response"
            }[x]
        )
        
        # Manual command input for command type
        manual_command = 0
        if code_type == "command":
            st.markdown("**Manual Command Input**")
            manual_command = st.number_input(
                "Command Code", 
                value=0, 
                min_value=0, 
                max_value=65535,
                help="Enter a custom command code (0-65535)"
            )
            
            # Common commands quick select
            st.markdown("**Quick Select Commands:**")
            col1a, col1b = st.columns(2)
            with col1a:
                if st.button("Status (0)", key="cmd_0"):
                    manual_command = 0
                if st.button("Start Op (1)", key="cmd_1"):
                    manual_command = 1
            with col1b:
                if st.button("Stop Op (2)", key="cmd_2"):
                    manual_command = 2
                if st.button("Auto Mode (3)", key="cmd_3"):
                    manual_command = 3
        
        # Generate button with Stow styling
        if st.button("🔄 Generate Code", type="primary"):
            with st.spinner(f"Generating {selected_language} code..."):
                generated_code = generate_protocol_code(
                    selected_language, 
                    code_type, 
                    host, 
                    port, 
                    manual_command
                )
                st.session_state.generated_code = generated_code
        
        # Manual test field
        st.markdown("---")
        st.markdown("""
        <div style="background: #fff3cd; padding: 1rem; border-radius: 8px; border-left: 4px solid #f39c12;">
            <h4 style="margin: 0; color: #856404;">🧪 Manual Test Command</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Spacing
        test_command = st.text_area(
            "Enter custom code to test",
            height=100,
            placeholder=f"Enter {selected_language} code here...",
            help="Enter your own TCP-IP communication code for testing"
        )
        
        if st.button("💾 Save Test Code"):
            if test_command.strip():
                st.session_state.generated_code = test_command
                st.success("✅ Test code saved successfully!")
            else:
                st.warning("⚠️ Please enter some code first")
    
    with col2:
        # Code display section
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #3498db;">
            <h3 style="margin: 0; color: #2c3e50;">📄 Generated {selected_language} Code</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")  # Spacing
        
        if st.session_state.generated_code:
            # Show file extension
            file_ext = get_file_extension(selected_language)
            st.markdown(f"""
            <div style="background: #d1ecf1; padding: 0.5rem; border-radius: 5px; margin-bottom: 1rem;">
                📁 <strong>Save as:</strong> <code>stow_wms_client{file_ext}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # Code display with syntax highlighting
            st.code(st.session_state.generated_code, language=selected_language.lower())
            
            # Download button
            st.download_button(
                label=f"📥 Download {selected_language} Code",
                data=st.session_state.generated_code,
                file_name=f"stow_wms_client{file_ext}",
                mime="text/plain"
            )
            
            # Copy to clipboard info
            st.info("💡 **Tip:** You can copy the code above and paste it into your IDE or development environment")
            
        else:
            st.markdown("""
            <div style="background: #e2e3e5; padding: 2rem; border-radius: 8px; text-align: center;">
                <h4>👆 Select a language and click 'Generate Code'</h4>
                <p>Your custom Stow WMS communication code will appear here</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Language-specific notes with Stow branding
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 1rem; border-radius: 10px; margin: 2rem 0;">
        <h3 style="margin: 0; color: #2c3e50;">📚 Stow Implementation Notes</h3>
    </div>
    """, unsafe_allow_html=True)
    
    language_notes = {
        "Node.js": """
        **Node.js Requirements for Stow WMS Integration:**
        - No additional packages needed (uses built-in `net` module)
        - Compatible with Node.js v12+ 
        - Execute with: `node stow_wms_client.js`
        - Perfect for Stow automation systems and IoT integration
        """,
        "C#": """
        **C# Requirements for Stow WMS Integration:**
        - .NET Core 3.1+ or .NET Framework 4.8+
        - Uses built-in `System.Net.Sockets`
        - Compile with: `csc stow_wms_client.cs` or use Visual Studio
        - Ideal for Stow enterprise applications and Windows services
        """,
        "Ruby": """
        **Ruby Requirements for Stow WMS Integration:**
        - Ruby 2.6+
        - Uses built-in `socket` library
        - Execute with: `ruby stow_wms_client.rb`
        - Great for Stow system automation and scripting
        """,
        "JavaScript": """
        **JavaScript (Browser) Requirements for Stow WMS Integration:**
        - Requires WebSocket-to-TCP proxy server
        - Cannot directly connect to TCP from browser
        - Perfect for Stow web dashboards and monitoring interfaces
        - Example proxy server setup included in generated code
        """,
        "Python": """
        **Python Requirements for Stow WMS Integration:**
        - Python 3.6+
        - Uses built-in `socket` library
        - Execute with: `python stow_wms_client.py`
        - Excellent for Stow data analysis and machine learning integration
        """
    }
    
    if selected_language in language_notes:
        st.markdown(language_notes[selected_language])

def render_diagnostics_page(current_status=None):
    """Render diagnostics page"""
    st.header("🔍 System Diagnostics")
    
    if current_status:
        st.success("📊 Real-time diagnostics with live connection")
    else:
        st.info("📋 Offline diagnostics mode")
    
    # Live diagnostics
    st.header("🔍 PLC Diagnostics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌐 Network Connectivity")
        
        if st.button("🔍 Test Connection"):
            host = st.session_state.get('host', '1.1.1.2')
            with st.spinner("Testing connectivity..."):
                # Simple ping test simulation
                import subprocess
                try:
                    result = subprocess.run(['ping', host, '-n', '1'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        st.success(f"✅ {host} is reachable")
                    else:
                        st.error(f"❌ {host} is not reachable")
                except:
                    st.error("❌ Ping test failed")
        
        if st.button("🔍 Scan Ports"):
            host = st.session_state.get('host', '1.1.1.2')
            common_ports = [102, 2000, 2001, 4840, 8080]
            
            with st.spinner("Scanning ports..."):
                port_results = []
                for port in common_ports:
                    # Simulate port scan
                    desc = {
                        102: "Siemens S7",
                        2000: "WMS Original",
                        2001: "WMS Alternative", 
                        4840: "OPC UA",
                        8080: "HTTP"
                    }.get(port, "Unknown")
                    
                    # Simple socket test
                    import socket
                    try:
                        sock = socket.socket()
                        sock.settimeout(1)
                        result = sock.connect_ex((host, port))
                        sock.close()
                        is_open = result == 0
                    except:
                        is_open = False
                    
                    port_results.append((port, desc, is_open))
                
                # Show results
                for port, desc, is_open in port_results:
                    if is_open:
                        st.success(f"✅ Port {port} ({desc}): OPEN")
                    else:
                        st.error(f"❌ Port {port} ({desc}): CLOSED")
    
    with col2:
        st.subheader("🏭 Mobile Racking Status")
        
        if current_status:
            # Show current system status
            if current_status.get('tcp_ip_connection'):
                st.success("✅ TCP-IP Connection Active")
            else:
                st.error("❌ TCP-IP Connection Failed")
                
            if current_status.get('power_on'):
                st.success("✅ System Power On")
            else:
                st.warning("⚠️ System Power Off")
        else:
            st.warning("⚠️ Mobile Racking TCP-IP service not detected")
            
            st.markdown("""
            **Probable causes:**
            - Mobile Racking software not running
            - TCP-IP server module not active  
            - Wrong port configuration
            - PLC in STOP mode
            
            **Required action:**
            Contact PLC technician to:
            1. Start Mobile Racking software
            2. Activate TCP-IP communication module
            3. Verify port configuration
            """)

def get_logo_base64():
    """Get base64 encoded logo for embedding"""
    import base64
    import os
    
    logo_path = "stow_logo.jpg"
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                logo_data = f.read()
            return base64.b64encode(logo_data).decode()
        except:
            pass
    
    # Fallback: return empty string if logo not found
    return ""

def main():
    """Main function with Stow branding"""
    
    # Header with Stow branding
    logo_b64 = get_logo_base64()
    if logo_b64:
        st.markdown(f"""
        <div class="main-header">
            <h1>
                <img src="data:image/jpeg;base64,{logo_b64}" class="stow-logo">
                Stow WMS Mobile Racking Controller
            </h1>
            <div class="header-subtitle">
                Advanced TCP-IP Communication Interface for Mobile Racking Systems
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-header">
            <h1>🏭 Stow WMS Mobile Racking Controller</h1>
            <div class="header-subtitle">
                Advanced TCP-IP Communication Interface for Mobile Racking Systems
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Render sidebar and get selected page
    selected_page = render_sidebar()
    
    # Route to selected page
    if selected_page == "💻 Code Generator":
        render_protocol_generator()
        return
    
    # Main content for other pages
    if st.session_state.connected:
        # Status indicator with Stow styling
        st.markdown("""
        <div style="background: #27ae60; color: white; padding: 1rem; border-radius: 8px; text-align: center; margin: 1rem 0;">
            <h3 style="margin: 0;">🟢 Stow System Connected & Operational</h3>
            <p style="margin: 0.5rem 0 0 0;">Mobile Racking system is online and responding</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Refresh button
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 Refresh Status"):
                get_system_status()
        
        # Get status if we're connected
        if st.button("📊 Get Status", type="primary") or st.session_state.last_status:
            status = get_system_status()
            
            if status or st.session_state.last_status:
                current_status = status or st.session_state.last_status
                
                if selected_page == "📊 Dashboard":
                    # Tabs for different views
                    tab1, tab2, tab3 = st.tabs([
                        "📊 Status Overview", "📋 Detailed View", "📈 History & Trends"
                    ])
                    
                    with tab1:
                        render_status_overview(current_status)
                    
                    with tab2:
                        render_detailed_status(current_status)
                    
                    with tab3:
                        render_history_chart()
                
                elif selected_page == "🎛️ Controls":
                    # Control tabs
                    tab1, tab2 = st.tabs([
                        "💡 Lighting Control", "🎛️ System Commands"
                    ])
                    
                    with tab1:
                        render_lighting_control(current_status)
                    
                    with tab2:
                        render_command_interface()
                
                elif selected_page == "🔍 Diagnostics":
                    render_diagnostics_page(current_status)
                
                # Timestamp with Stow styling
                if 'timestamp' in current_status:
                    st.sidebar.markdown(f"""
                    <div style="background: #ecf0f1; padding: 0.5rem; border-radius: 5px; text-align: center; margin-top: 1rem;">
                        🕒 Last update: {current_status['timestamp'].strftime('%H:%M:%S')}
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        # Disconnected state with Stow styling
        st.markdown("""
        <div style="background: #e74c3c; color: white; padding: 1rem; border-radius: 8px; text-align: center; margin: 1rem 0;">
            <h3 style="margin: 0;">🔴 Stow System Disconnected</h3>
            <p style="margin: 0.5rem 0 0 0;">Please establish connection to access Mobile Racking controls</p>
        </div>
        """, unsafe_allow_html=True)
        
        if selected_page == "🔍 Diagnostics":
            render_diagnostics_page()
        elif selected_page == "💻 Code Generator":
            render_protocol_generator()
        else:
            # Check if in cloud environment
            import os
            is_cloud = os.getenv('STREAMLIT_SHARING') or 'streamlit.app' in os.getenv('HOSTNAME', '')
            
            if is_cloud:
                # Cloud-specific welcome message
                st.markdown("""
                <div style="background: linear-gradient(135deg, #3498db, #2980b9); padding: 2rem; border-radius: 10px; color: white; margin: 2rem 0;">
                    <h2 style="margin: 0; text-align: center;">🌐 Stow WMS Demo Environment</h2>
                    <p style="margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">Experience the interface - Download for full PLC connectivity</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Demo limitations notice
                st.markdown("""
                <div class="metric-card" style="border-left: 4px solid #f39c12;">
                    <h3 style="color: #f39c12; margin-top: 0;">📋 Demo Environment Notice</h3>
                    <p style="margin: 0.5rem 0;">This is a demonstration version running on Streamlit Community Cloud. 
                    TCP-IP connections to external PLC systems are not available in this environment.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # What works in cloud
                st.markdown("### ✅ Available Features in Cloud Demo:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("**💻 Code Generator** - Generate integration code for 5 programming languages")
                    st.success("**📖 Documentation** - Complete setup guides and examples")
                
                with col2:
                    st.success("**🎨 Interface Preview** - See the full Stow-branded interface")
                    st.success("**📊 Feature Overview** - Explore all available capabilities")
                
                # Download instructions
                st.markdown("### 🚀 Get Full Functionality:")
                
                st.markdown("""
                <div class="metric-card" style="border-left: 4px solid #27ae60;">
                    <h4 style="color: #27ae60; margin-top: 0;">📥 Download for PLC Connectivity</h4>
                    <ol>
                        <li><strong>Clone Repository:</strong> <code>git clone https://github.com/COVDB/WMS-Node.JS.git</code></li>
                        <li><strong>Install Dependencies:</strong> <code>pip install -r requirements.txt</code></li>
                        <li><strong>Run Locally:</strong> <code>streamlit run app.py</code></li>
                        <li><strong>Connect to PLC:</strong> Full TCP-IP connectivity available</li>
                    </ol>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                # Local environment - original quick start guide
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f8f9fa, #e9ecef); padding: 2rem; border-radius: 10px; margin: 2rem 0;">
                    <h2 style="color: #2c3e50; margin-top: 0;">🚀 Stow Mobile Racking Quick Start Guide</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Welcome section with proper Streamlit styling
                st.markdown("""
                <div class="metric-card" style="margin: 1rem 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">Welcome to the Stow WMS Mobile Racking Control System</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Getting started steps
                st.markdown("#### 📋 Getting Started:")
                st.markdown("""
                1. **Configure Connection:** Set IP address and port in the sidebar
                2. **Connect:** Click the Connect button to establish communication  
                3. **Navigate:** Use the sidebar to access different system areas
                """)
            
            # System areas with proper Streamlit columns
            st.markdown("### 🏭 System Areas Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #3498db;">📊 Dashboard</h4>
                    <p style="margin: 0.5rem 0 0 0;">Real-time status monitoring and system overview with live metrics</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")  # Spacing
                
                st.markdown("""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #e67e22;">🔍 Diagnostics</h4>
                    <p style="margin: 0.5rem 0 0 0;">Network analysis and troubleshooting tools for system health</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #27ae60;">🎛️ Controls</h4>
                    <p style="margin: 0.5rem 0 0 0;">System operations and lighting management interface</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")  # Spacing
                
                st.markdown("""
                <div class="metric-card">
                    <h4 style="margin: 0; color: #8e44ad;">� Code Generator</h4>
                    <p style="margin: 0.5rem 0 0 0;">Multi-language integration code for various platforms</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Pro tips section
            st.markdown("### 💡 Pro Tips")
            st.info("**🚀 Try the Code Generator** - Works without connection and generates code for Node.js, C#, Ruby, JavaScript, and Python!")
            st.info("**🔧 Use Diagnostics** - Troubleshoot connection issues with built-in network tools")
            st.info("**📞 Stow Support** - Contact our technical team for assistance with Mobile Racking systems")
            
            # Footer with Stow branding
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; margin-top: 2rem;">
                <p style="color: #666; font-size: 0.9rem;">
                    <strong>Stow Group</strong> - Leading provider of innovative storage solutions<br>
                    <span style="color: #ff6b35;">Powered by advanced automation technology</span>
                </p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
