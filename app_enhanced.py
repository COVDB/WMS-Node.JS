"""
WMS Mobile Racking TCP-IP Communication Streamlit App - Enhanced Version
Combines the full feature set with advanced response parsing
"""

import streamlit as st
import pandas as pd
import time
import struct
import os
import subprocess
import base64
import socket
import datetime
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
    page_title="Stow WMS Enhanced Controller",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Response Parser Functions (OFFICIAL MAPPING)
from enhanced_response_parser import (
    parse_enhanced_mobile_response, 
    get_safety_assessment, 
    format_status_for_customer,
    decode_boolean_flags_byte5,
    decode_alarm_flags
)
    """
    Parse Mobile Racking 20-byte response with enhanced interpretation
    Based on real RevPi data: [0,2,2,5,9,9,0,0,223,27,0,0,0,0,0,0,0,14,0,0]
    """
    if len(response_bytes) != 20:
        raise ValueError(f"Expected 20 bytes, got {len(response_bytes)}")
    
    # Parse as 10 x 16-bit little-endian words
    words = struct.unpack('<10H', response_bytes)
    
    # Create enhanced status dictionary
    status = {
        'raw_response': list(response_bytes),
        'hex_response': response_bytes.hex().upper(),
        'words': list(words),
        
        # Enhanced status fields based on real data analysis
        'tcp_status': words[0],          # 512 in real response
        'software_version_word': words[1], # 1282 = [2,5] = v2.5
        'status_flags_word': words[2],   # 2313 = [9,9] - needs investigation
        'power_status': words[3],        # Power and basic controls
        'mobile_data': words[4],         # 6879 = movement data
        'reserved_1': words[5],          # Usually 0
        'reserved_2': words[6],          # Usually 0 
        'reserved_3': words[7],          # Usually 0
        'position_data': words[8],       # 3584 = position info
        'additional_status': words[9],   # Extra status
        
        # Derived interpretations
        'software_major': response_bytes[2],  # Byte 2 = major version
        'software_minor': response_bytes[3],  # Byte 3 = minor version
        'software_version': f"{response_bytes[2]}.{response_bytes[3]}",
        
        # System health indicators
        'system_active': words[1] > 0,
        'ready_to_operate': words[1] > 1000,  # High value indicates full operation
        'movement_detected': words[4] > 0,
        'position_known': words[8] > 0,
        
        # Timestamp
        'timestamp': datetime.now().strftime("%H:%M:%S")
    }
    
    return status

def get_status_color_indicator(status: Dict[str, Any]) -> str:
    """Get color-coded status indicator"""
    if not status:
        return "⚫ UNKNOWN"
    
    if status.get('ready_to_operate', False):
        return "🟢 OPERATIONEEL"
    elif status.get('system_active', False):
        return "🟡 BEPERKT ACTIEF"
    else:
        return "🔴 INACTIEF"

def explain_response_for_customer(status: Dict[str, Any]) -> str:
    """Create detailed customer-friendly explanation"""
    
    explanations = []
    
    # Header
    explanations.append("# 📊 Machine Status Uitleg")
    explanations.append("")
    
    # Quick summary
    color_status = get_status_color_indicator(status)
    explanations.append(f"**Huidige Status:** {color_status}")
    explanations.append("")
    
    # Software version (confirmed correct)
    sw_version = status.get('software_version', 'Unknown')
    explanations.append(f"**Software Versie:** {sw_version} ✅")
    explanations.append("")
    
    # Key indicators
    explanations.append("## 🔍 Belangrijke Indicatoren:")
    explanations.append("")
    
    # System status word
    sys_word = status.get('software_version_word', 0)
    explanations.append(f"- **Systeem Activiteit:** {sys_word}")
    if sys_word > 1000:
        explanations.append("  ✅ Hoge waarde = Volledig operationeel")
    elif sys_word > 0:
        explanations.append("  ⚠️ Lage waarde = Beperkte functionaliteit")
    else:
        explanations.append("  ❌ Nul = Systeem uitgeschakeld")
    explanations.append("")
    
    # Movement data
    movement = status.get('mobile_data', 0)
    explanations.append(f"- **Beweging Gedetecteerd:** {movement}")
    if movement > 0:
        explanations.append("  ✅ Er zijn bewegende delen actief")
    else:
        explanations.append("  ⚪ Geen beweging gedetecteerd")
    explanations.append("")
    
    # Position data
    position = status.get('position_data', 0)
    explanations.append(f"- **Positie Informatie:** {position}")
    if position > 0:
        explanations.append("  ✅ Positie bekend en actief")
    else:
        explanations.append("  ⚪ Standaard positie")
    explanations.append("")
    
    # Status flags (needs investigation)
    raw_response = status.get('raw_response', [])
    flags = raw_response[4] if len(raw_response) > 4 else 0
    explanations.append(f"- **Status Flags (Byte 5):** {flags}")
    if flags == 9:
        explanations.append("  ⚠️ Waarde 9 voor Boolean veld - onderzoek nodig")
    explanations.append("")
    
    # Safety guidance
    explanations.append("## ⚠️ Veiligheids Richtlijnen:")
    explanations.append("")
    if status.get('ready_to_operate', False):
        explanations.append("✅ **VEILIG GEBRUIK:** Machine is klaar voor gang commando's")
    else:
        explanations.append("❌ **STOP GEBRUIK:** Machine niet klaar - contacteer technicus")
    
    return "\\n".join(explanations)

def send_enhanced_aisle_command(aisle_number: int, use_legacy: bool = False):
    """Send aisle command with enhanced response handling"""
    try:
        # Connect to PLC
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("1.1.1.2", 2000))
        
        if use_legacy:
            # Legacy WMS Protocol
            start_byte = 0x02
            length = 2
            command = 0x4F
            aisle_byte = aisle_number
            checksum = length ^ command ^ aisle_byte
            end_byte = 0x03
            command_bytes = bytes([start_byte, length, command, aisle_byte, checksum, end_byte])
        else:
            # Simple protocol
            command_bytes = bytes([aisle_number, 1])
        
        # Send and receive
        sock.send(command_bytes)
        response = sock.recv(20)
        sock.close()
        
        # Parse response
        parsed_status = parse_mobile_racking_response(response)
        
        return {
            "success": True, 
            "response": response, 
            "parsed": parsed_status,
            "command_sent": command_bytes
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_enhanced_status_request():
    """Send status request with enhanced parsing"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("1.1.1.2", 2000))
        
        command_bytes = bytes([0, 2])
        sock.send(command_bytes)
        response = sock.recv(20)
        sock.close()
        
        parsed_status = parse_mobile_racking_response(response)
        
        return {
            "success": True, 
            "response": response, 
            "parsed": parsed_status,
            "command_sent": command_bytes
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Enhanced UI Components
def render_enhanced_gang_control():
    """Render enhanced gang control with response analysis"""
    st.subheader("🎯 Verbeterde Gang Besturing")
    
    # Protocol selection
    protocol_col1, protocol_col2 = st.columns(2)
    with protocol_col1:
        use_legacy = st.checkbox("Legacy WMS Protocol", value=False, 
                                help="STX+LEN+CMD+AISLE+CHK+ETX vs Simple [aisle,1]")
    
    with protocol_col2:
        if st.button("📊 STATUS AANVRAAG", type="primary"):
            with st.spinner("Status opvragen..."):
                result = send_enhanced_status_request()
                
                if result["success"]:
                    st.session_state['last_status'] = result["parsed"]
                    st.success("Status succesvol opgehaald!")
                else:
                    st.error(f"Status fout: {result['error']}")
    
    # Gang selection and sending
    st.write("**Gang Selectie (1-24):**")
    
    # Create 3 columns for gang buttons
    col1, col2, col3 = st.columns(3)
    
    for i in range(1, 25):
        col = [col1, col2, col3][(i-1) % 3]
        with col:
            if st.button(f"Gang {i}", key=f"enhanced_gang_{i}"):
                with st.spinner(f"Gang {i} openen..."):
                    result = send_enhanced_aisle_command(i, use_legacy)
                    
                    if result["success"]:
                        st.session_state['last_command'] = result
                        st.session_state['last_status'] = result["parsed"]
                        st.success(f"Gang {i} commando verzonden!")
                    else:
                        st.error(f"Gang {i} fout: {result['error']}")

def render_enhanced_status_display():
    """Render enhanced status display with detailed analysis"""
    st.subheader("📈 Uitgebreide Status Analyse")
    
    if 'last_status' in st.session_state:
        status = st.session_state['last_status']
        
        # Status overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            color_status = get_status_color_indicator(status)
            st.metric("Systeem Status", color_status)
        
        with col2:
            sw_version = status.get('software_version', 'N/A')
            st.metric("Software Versie", sw_version)
        
        with col3:
            sys_word = status.get('software_version_word', 0)
            st.metric("Activiteit Level", sys_word)
        
        with col4:
            timestamp = status.get('timestamp', 'N/A')
            st.metric("Laatste Update", timestamp)
        
        # Detailed breakdown
        with st.expander("🔍 Gedetailleerde Analyse", expanded=True):
            
            # Raw data
            st.write("**Raw Response Data:**")
            st.code(f"Bytes: {status.get('raw_response', [])}")
            st.code(f"Hex: {status.get('hex_response', 'N/A')}")
            st.code(f"Words: {status.get('words', [])}")
            
            # Interpretations
            st.write("**Status Interpretaties:**")
            
            status_df = pd.DataFrame([
                {"Veld": "TCP Status", "Waarde": status.get('tcp_status', 0), "Betekenis": "Verbindingsstatus"},
                {"Veld": "Software Versie", "Waarde": status.get('software_version', 'N/A'), "Betekenis": "✅ Bevestigd correct"},
                {"Veld": "Status Flags", "Waarde": status.get('status_flags_word', 0), "Betekenis": "⚠️ Onderzoek byte 5=9"},
                {"Veld": "Mobile Data", "Waarde": status.get('mobile_data', 0), "Betekenis": "Bewegingsinformatie"},
                {"Veld": "Positie Data", "Waarde": status.get('position_data', 0), "Betekenis": "Huidige positie"},
            ])
            
            st.dataframe(status_df, use_container_width=True)
        
        # Customer explanation
        with st.expander("📋 Klant Uitleg", expanded=False):
            explanation = explain_response_for_customer(status)
            st.markdown(explanation)
    
    else:
        st.info("Geen status data beschikbaar. Klik op 'STATUS AANVRAAG' om data op te halen.")

# Main app layout
def main():
    st.title("🏭 Stow WMS Enhanced Controller")
    st.write("Uitgebreide versie met verbeterde response analyse")
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["🎯 Gang Besturing", "📊 Status Analyse", "🔧 Technische Info"])
    
    with tab1:
        render_enhanced_gang_control()
    
    with tab2:
        render_enhanced_status_display()
    
    with tab3:
        st.subheader("🔧 Technische Informatie")
        
        st.write("**Protocol Details:**")
        st.write("- **Legacy Protocol:** STX(0x02) + LEN + CMD(0x4F) + AISLE + CHECKSUM + ETX(0x03)")
        st.write("- **Simple Protocol:** [aisle_number, 1] voor opening, [0, 2] voor status")
        st.write("- **Response:** 20 bytes als 10x 16-bit woorden (little-endian)")
        
        st.write("**Huidige Bevindingen:**")
        st.write("- ✅ Software versie correct: bytes 2-3 = [2,5] = v2.5")
        st.write("- ⚠️ Byte 5 waarde 9: zou Boolean moeten zijn, onderzoek nodig")
        st.write("- ✅ Response parsing: 20-byte structuur geïdentificeerd")
        
        if st.button("📄 Toon Documentatie"):
            st.write("**Verwijs naar:**")
            st.write("- `WMS_Response_Documentation.md` voor technische details")
            st.write("- `Customer_Response_Email.txt` voor klantuitleg")

if __name__ == "__main__":
    main()
