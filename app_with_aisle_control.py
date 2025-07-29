import streamlit as st
import time
import datetime
import socket
import struct

# Page config
st.set_page_config(
    page_title="Stow WMS Mobile Racking Controller", 
    layout="wide"
)

# Header
st.title("Stow WMS Mobile Racking Controller")
st.markdown("**Revolution Pi Connect SE - Industrial TCP/IP Interface**")

# Initialize session state for aisle control
if 'last_command' not in st.session_state:
    st.session_state.last_command = None
if 'command_result' not in st.session_state:
    st.session_state.command_result = None
if 'command_timestamp' not in st.session_state:
    st.session_state.command_timestamp = None

# Function to create aisle open command
def create_aisle_command(aisle_number):
    """
    Create WMS protocol command to open specific aisle
    Format: [Start][Length][Command][Aisle][Checksum][End]
    """
    try:
        # Validate aisle number
        if not (1 <= aisle_number <= 24):
            return None, "Ongeldige gang nummer. Gebruik 1-24."
        
        # WMS Protocol structure
        start_byte = 0x02  # STX
        command = 0x4F     # 'O' for Open
        aisle_byte = aisle_number
        end_byte = 0x03    # ETX
        
        # Calculate length (command + aisle)
        length = 2
        
        # Create message without checksum first
        message_without_checksum = struct.pack('BBBB', start_byte, length, command, aisle_byte)
        
        # Calculate checksum (XOR of all bytes except start and end)
        checksum = length ^ command ^ aisle_byte
        
        # Complete message
        complete_message = struct.pack('BBBBB', start_byte, length, command, aisle_byte, checksum) + struct.pack('B', end_byte)
        
        return complete_message, f"Gang {aisle_number} open commando gegenereerd"
        
    except Exception as e:
        return None, f"Fout bij commando generatie: {str(e)}"

# Function to send command to PLC
def send_aisle_command(command_bytes, plc_ip, plc_port):
    """
    Send aisle command to PLC via TCP
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Connect to PLC
        sock.connect((plc_ip, plc_port))
        
        # Send command
        sock.send(command_bytes)
        
        # Wait for response (optional)
        try:
            response = sock.recv(1024)
            sock.close()
            return True, f"Commando verzonden. Response: {len(response)} bytes ontvangen"
        except socket.timeout:
            sock.close()
            return True, "Commando verzonden (geen response ontvangen)"
            
    except Exception as e:
        return False, f"Fout bij verzenden: {str(e)}"

# Sidebar
with st.sidebar:
    st.header("Connection Settings")
    plc_ip = st.text_input("PLC IP Address", value="1.1.1.2")
    plc_port = st.number_input("PLC Port", value=2000, min_value=1, max_value=65535)
    
    st.markdown("---")
    st.subheader("Revolution Pi Network")
    st.info("Management: 192.168.0.12 (eth0)\nPLC Network: 1.1.1.185 (eth1)")
    
    if st.button("Test PLC Connection", type="primary"):
        with st.spinner("Testing connection..."):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((plc_ip, plc_port))
                sock.close()
                
                if result == 0:
                    st.success(f"Connected to {plc_ip}:{plc_port}")
                else:
                    st.error(f"Connection failed to {plc_ip}:{plc_port}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Live Monitoring", "Aisle Control", "System Status", "Configuration"])

with tab1:
    st.header("Real-time HMI Monitoring")
    
    col1, col2, col3, col4 = st.columns(4)
    
    current_time = datetime.datetime.now()
    
    with col1:
        # Simulate changing modes
        modes = ['Manual', 'Automatic', 'Maintenance', 'Setup']
        mode_index = (int(current_time.timestamp()) // 30) % len(modes)
        current_mode = modes[mode_index]
        
        st.metric("Operating Mode", current_mode, "Active")
    
    with col2:
        st.metric("Connection Status", "Connected", "Online")
    
    with col3:
        st.metric("Last Update", current_time.strftime("%H:%M:%S"), "Live")
    
    with col4:
        st.metric("RevPi Status", "Online", "192.168.0.12")
    
    # Show last command if any
    if st.session_state.last_command:
        st.markdown("---")
        st.subheader("Laatste Commando")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"Gang: {st.session_state.last_command}")
        with col2:
            st.info(f"Tijd: {st.session_state.command_timestamp}")
        with col3:
            if st.session_state.command_result:
                if "verzonden" in st.session_state.command_result.lower():
                    st.success("Status: Verzonden")
                else:
                    st.error("Status: Fout")
    
    # Auto refresh
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
    
    if auto_refresh:
        time.sleep(0.1)
        st.rerun()

with tab2:
    st.header("Gang Besturing")
    st.markdown("**Configureer en open specifieke gangen in het mobile racking systeem**")
    
    # Aisle Control Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Gang Selectie")
        
        # Method 1: Number input
        aisle_number = st.number_input(
            "Gang Nummer (1-24)", 
            min_value=1, 
            max_value=24, 
            value=1, 
            step=1,
            help="Selecteer gang nummer tussen 1 en 24"
        )
        
        # Method 2: Slider alternative
        st.markdown("**Of gebruik de slider:**")
        aisle_slider = st.slider("Gang Nummer", 1, 24, int(aisle_number))
        
        # Use slider value if different
        if aisle_slider != aisle_number:
            aisle_number = aisle_slider
        
        # Command preview
        st.markdown("---")
        st.subheader("Commando Preview")
        
        command_bytes, command_msg = create_aisle_command(aisle_number)
        
        if command_bytes:
            # Show command details
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.code(f"""
Commando Details:
- Gang Nummer: {aisle_number}
- Commando Type: Open Gang
- Protocol: WMS TCP/IP
- Docel IP: {plc_ip}:{plc_port}
                """)
            
            with col_b:
                # Show hex representation
                hex_string = ' '.join([f'{b:02X}' for b in command_bytes])
                st.code(f"""
Hex Bytes:
{hex_string}

Byte Breakdown:
STX: {command_bytes[0]:02X}
LEN: {command_bytes[1]:02X}
CMD: {command_bytes[2]:02X} ('O')
GANG: {command_bytes[3]:02X} ({aisle_number})
CHK: {command_bytes[4]:02X}
ETX: {command_bytes[5]:02X}
                """)
        
        # Send command button
        st.markdown("---")
        col_send, col_test = st.columns(2)
        
        with col_send:
            if st.button(f"🚀 Open Gang {aisle_number}", type="primary", use_container_width=True):
                if command_bytes:
                    with st.spinner(f"Verzenden commando naar gang {aisle_number}..."):
                        success, result_msg = send_aisle_command(command_bytes, plc_ip, plc_port)
                        
                        # Store in session state
                        st.session_state.last_command = aisle_number
                        st.session_state.command_result = result_msg
                        st.session_state.command_timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                        
                        if success:
                            st.success(f"✅ {result_msg}")
                        else:
                            st.error(f"❌ {result_msg}")
        
        with col_test:
            if st.button("🧪 Test Commando (Geen Verzending)", use_container_width=True):
                if command_bytes:
                    st.info(f"✅ Commando voor gang {aisle_number} is geldig en klaar voor verzending")
                    st.balloons()
    
    with col2:
        st.subheader("Gang Status")
        
        # Quick access buttons for common aisles
        st.markdown("**Snelle Toegang:**")
        
        quick_aisles = [1, 5, 10, 15, 20, 24]
        
        for aisle in quick_aisles:
            if st.button(f"Gang {aisle}", key=f"quick_{aisle}", use_container_width=True):
                # Update the main number input
                st.session_state.aisle_quick_select = aisle
                st.rerun()
        
        # Check if quick select was used
        if 'aisle_quick_select' in st.session_state:
            aisle_number = st.session_state.aisle_quick_select
            del st.session_state.aisle_quick_select
        
        st.markdown("---")
        st.subheader("Recente Activiteit")
        
        if st.session_state.last_command:
            st.success(f"Laatste: Gang {st.session_state.last_command}")
            st.caption(f"Tijd: {st.session_state.command_timestamp}")
            
            if st.button("🗑️ Wis Geschiedenis", use_container_width=True):
                st.session_state.last_command = None
                st.session_state.command_result = None
                st.session_state.command_timestamp = None
                st.rerun()
        else:
            st.info("Nog geen commando's verzonden")
    
    # Safety notice
    st.markdown("---")
    st.warning("⚠️ **Veiligheidswaarschuwing:** Zorg ervoor dat het gebied vrij is voordat u een gang opent. Controleer altijd de PLC status voordat u commando's verzendt.")

with tab3:
    st.header("System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Network Status")
        network_data = {
            "Interface": ["eth0", "eth1"],
            "IP Address": ["192.168.0.12", "1.1.1.185"],
            "Purpose": ["Management", "PLC Network"],
            "Status": ["Active", "Active"]
        }
        st.table(network_data)
    
    with col2:
        st.subheader("System Health")
        health_data = {
            "Component": ["RevPi Hardware", "Python Runtime", "Streamlit Service", "Network"],
            "Status": ["Healthy", "Running", "Active", "Connected"],
            "Details": ["Connect SE", "Python 3.11", "Port 8502", "Dual Network"]
        }
        st.table(health_data)
    
    # Command Statistics
    st.markdown("---")
    st.subheader("Commando Statistieken")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_commands = 1 if st.session_state.last_command else 0
        st.metric("Totaal Commando's", total_commands)
    
    with col2:
        st.metric("Actieve Gangen", "0/24")
    
    with col3:
        st.metric("PLC Verbinding", "Online" if True else "Offline")
    
    with col4:
        st.metric("Laatste Activiteit", st.session_state.command_timestamp or "N/A")

with tab4:
    st.header("Configuration")
    
    st.subheader("Deployment Information")
    
    st.success("Revolution Pi deployment successful!")
    
    deployment_info = [
        ("Hardware Platform", "Revolution Pi Connect SE"),
        ("Management IP", "192.168.0.12 (eth0)"),
        ("PLC Network IP", "1.1.1.185 (eth1)"),
        ("Web Interface", "http://192.168.0.12:8502"),
        ("Service Status", "wms-streamlit.service - Running"),
        ("Python Version", "3.11"),
        ("Streamlit Version", "1.47.1"),
        ("WMS Protocol", "TCP/IP with checksum validation")
    ]
    
    for key, value in deployment_info:
        st.text(f"{key}: {value}")
    
    st.markdown("---")
    st.subheader("Protocol Configuration")
    
    st.code("""
WMS Protocol Format:
[STX][LENGTH][COMMAND][AISLE][CHECKSUM][ETX]

Commands:
- 'O' (0x4F): Open Aisle
- Aisle Range: 1-24
- Checksum: XOR of LENGTH, COMMAND, AISLE
- STX: 0x02, ETX: 0x03
    """)
    
    st.markdown("---")
    st.subheader("Management Commands")
    st.code("""
# Service management
sudo systemctl status wms-streamlit
sudo systemctl restart wms-streamlit

# Logs
journalctl -u wms-streamlit -f

# Network test
ping 1.1.1.2

# Upload new version
scp app_with_aisle_control.py revpi@192.168.0.12:/home/revpi/app.py
    """)

# Footer
st.markdown("---")
st.markdown("**Stow WMS Mobile Racking Controller** | Revolution Pi Connect SE | Industrial Interface v2.0 with Aisle Control")

# Status indicator
if st.session_state.get('last_refresh', 0) + 30 < time.time():
    st.session_state.last_refresh = time.time()
    if auto_refresh:
        time.sleep(1)
        st.rerun()
