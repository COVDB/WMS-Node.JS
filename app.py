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
    """Create connection to Mobile Racking controller"""
    host = st.session_state.get('host', '1.1.1.2')
    port = st.session_state.get('port', 2000)
    
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
    st.sidebar.header("🔌 Connection")
    
    # Connection configuration
    host = st.sidebar.text_input("IP Address", value="1.1.1.2", key="host")
    
    # Port selection with detection
    st.sidebar.write("**Port Configuration:**")
    port_option = st.sidebar.radio(
        "Select port:",
        ["2001 (Detected ✅)", "2000 (Original)", "Custom"],
        key="port_option"
    )
    
    if port_option == "2001 (Detected ✅)":
        port = 2001
        st.sidebar.success("Port 2001 detected as open!")
    elif port_option == "2000 (Original)":
        port = 2000
        st.sidebar.warning("Port 2000 appears closed")
    else:  # Custom
        port = st.sidebar.number_input("Custom port:", min_value=1, max_value=65535, value=2001)
    
    st.session_state.port = port
    
    # Connection status indicator
    if st.session_state.connected:
        st.sidebar.success(f"🟢 Connected to {host}:{port}")
    else:
        st.sidebar.error("🔴 Not connected")
    
    # Connection buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Connect", type="primary", disabled=st.session_state.connected):
            create_connection()
    
    with col2:
        if st.button("Disconnect", disabled=not st.session_state.connected):
            disconnect()
    
    st.sidebar.divider()
    
    # Quick port scan
    st.sidebar.header("🔍 Diagnostics")
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

def render_status_overview(status: Dict[str, Any]):
    """Render status overview"""
    st.header("📊 System Status")
    
    # Validation
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
        st.metric("TCP-IP Connection", tcp_status)
    
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

def main():
    """Main function"""
    st.title("🏭 WMS Mobile Racking Controller")
    st.markdown("TCP-IP communication interface for Mobile Racking systems")
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    if st.session_state.connected:
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
                
                # Tabs for different views
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "Status Overview", "Detailed", "Lighting Control", 
                    "Commands", "History"
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
                    st.sidebar.write(f"Last update: {current_status['timestamp'].strftime('%H:%M:%S')}")
    
    else:
        st.info("👆 Connect first via the sidebar")
        
        # Show live diagnostics
        st.header("🔍 PLC Diagnostics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📡 Network Status")
            
            # Test basic connectivity
            if st.button("🏓 Test Ping"):
                with st.spinner("Testing ping..."):
                    import subprocess
                    try:
                        result = subprocess.run(
                            ['ping', '1.1.1.2', '-n', '2'], 
                            capture_output=True, text=True, timeout=10
                        )
                        if result.returncode == 0:
                            st.success("✅ Ping successful - network OK")
                        else:
                            st.error("❌ Ping failed - network problem")
                    except Exception as e:
                        st.error(f"Ping test error: {e}")
            
            # Test ports
            if st.button("🔍 Scan Ports"):
                with st.spinner("Scanning ports..."):
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
                    
                    # Show results
                    for port, desc, is_open, rt in port_results:
                        if is_open:
                            st.success(f"✅ Port {port} ({desc}): OPEN ({rt:.0f}ms)")
                        else:
                            st.error(f"❌ Port {port} ({desc}): CLOSED")
        
        with col2:
            st.subheader("🏭 Mobile Racking Status")
            
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
        
        # Show example data
        st.header("📖 Example WMS Data Structure")
        
        example_data = []
        for key, field in list(WMS_DATA_STRUCTURE.items())[:10]:  # Show first 10
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
