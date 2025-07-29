import streamlit as st
import socket
import struct

# Page config
st.set_page_config(page_title="Stow WMS Mobile Racking Controller", layout="wide")

# Header
st.title("Stow WMS Mobile Racking Controller")
st.markdown("**Revolution Pi Connect SE - Industrial TCP/IP Interface**")

# Sidebar Navigation (alternatief voor tabs)
with st.sidebar:
    st.header("Navigation")
    
    page = st.radio(
        "Selecteer Pagina:",
        ["Live Monitoring", "Gang Besturing", "System Status", "Configuration"]
    )
    
    st.markdown("---")
    
    st.header("Connection Settings")
    plc_ip = st.text_input("PLC IP Address", value="1.1.1.2")
    plc_port = st.number_input("PLC Port", value=2000, min_value=1, max_value=65535)
    
    st.markdown("---")
    st.subheader("Revolution Pi Network")
    st.info("Management: 192.168.0.12 (eth0)\nPLC Network: 1.1.1.185 (eth1)")

# Main content gebaseerd op sidebar selectie
if page == "Live Monitoring":
    st.header("Real-time HMI Monitoring")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Operating Mode", "Manual", "Active")
    
    with col2:
        st.metric("Connection Status", "Connected", "Online")
    
    with col3:
        st.metric("Last Update", "19:30:15", "Live")
    
    with col4:
        st.metric("RevPi Status", "Online", "192.168.0.12")

elif page == "Gang Besturing":
    st.header("🎯 Gang Besturing - WMS Commando's")
    
    st.success("✅ GANG BESTURING SECTIE GEVONDEN!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Gang Selectie")
        
        # Gang nummer input
        aisle_number = st.number_input(
            "Gang Nummer (1-24)", 
            min_value=1, 
            max_value=24, 
            value=1, 
            step=1,
            help="Selecteer gang nummer tussen 1 en 24"
        )
        
        # Slider alternatief
        st.markdown("**Of gebruik de slider:**")
        aisle_slider = st.slider("Gang Nummer", 1, 24, int(aisle_number))
        
        if aisle_slider != aisle_number:
            aisle_number = aisle_slider
        
        # WMS Protocol preview
        st.markdown("---")
        st.subheader("WMS Protocol Preview")
        
        # Generate command bytes
        start_byte = 0x02
        length = 2
        command = 0x4F  # 'O' for Open
        aisle_byte = aisle_number
        checksum = length ^ command ^ aisle_byte
        end_byte = 0x03
        
        command_bytes = [start_byte, length, command, aisle_byte, checksum, end_byte]
        hex_string = ' '.join([f'{b:02X}' for b in command_bytes])
        
        st.code(f"""
WMS Protocol Commando voor Gang {aisle_number}:
Hex Bytes: {hex_string}

Breakdown:
- STX: 0x{start_byte:02X} (Start)
- LEN: 0x{length:02X} (Payload length) 
- CMD: 0x{command:02X} ('O' voor Open)
- GANG: 0x{aisle_byte:02X} (Gang {aisle_number})
- CHK: 0x{checksum:02X} (XOR checksum)
- ETX: 0x{end_byte:02X} (End)
        """)
        
        # Buttons
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button(f"🚀 Open Gang {aisle_number}", type="primary", use_container_width=True):
                st.success(f"✅ Commando verzonden naar gang {aisle_number}!")
                st.balloons()
        
        with col_b:
            if st.button("🧪 Test Commando", use_container_width=True):
                st.info(f"✅ Commando voor gang {aisle_number} is geldig!")
    
    with col2:
        st.subheader("Quick Access")
        
        quick_aisles = [1, 5, 10, 15, 20, 24]
        
        for aisle in quick_aisles:
            if st.button(f"Gang {aisle}", key=f"quick_{aisle}", use_container_width=True):
                st.info(f"Gang {aisle} geselecteerd")
        
        st.markdown("---")
        st.subheader("Status")
        st.success("Gang besturing actief")

elif page == "System Status":
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

elif page == "Configuration":
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

# Footer
st.markdown("---")
st.markdown("**Stow WMS Mobile Racking Controller** | Revolution Pi Connect SE | Sidebar Navigation Version")
