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

# Main content - TEST WITH 4 TABS
tab1, tab2, tab3, tab4 = st.tabs(["Live Monitoring", "Aisle Control", "System Status", "Configuration"])

with tab1:
    st.header("Real-time HMI Monitoring")
    
    col1, col2, col3, col4 = st.columns(4)
    
    current_time = datetime.datetime.now()
    
    with col1:
        st.metric("Operating Mode", "Manual", "Active")
    
    with col2:
        st.metric("Connection Status", "Connected", "Online")
    
    with col3:
        st.metric("Last Update", current_time.strftime("%H:%M:%S"), "Live")
    
    with col4:
        st.metric("RevPi Status", "Online", "192.168.0.12")

with tab2:
    st.header("Gang Besturing - TEST TAB")
    
    st.success("✅ Deze tab is zichtbaar! Gang besturing functionaliteit werkt.")
    
    # Simple aisle selection
    aisle_number = st.number_input("Gang Nummer (1-24)", min_value=1, max_value=24, value=1)
    
    if st.button(f"Test Gang {aisle_number}", type="primary"):
        st.success(f"Gang {aisle_number} commando getest!")
        st.balloons()

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

with tab4:
    st.header("Configuration")
    
    st.subheader("Test Deployment")
    
    st.success("✅ 4 Tabs Test - Gang Besturing Tab is zichtbaar!")
    
    st.info("Als je deze tab ziet, dan werkt de 4-tab layout correct.")

# Footer
st.markdown("---")
st.markdown("**Stow WMS Mobile Racking Controller** | Revolution Pi Connect SE | Test Version")
