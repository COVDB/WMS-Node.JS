"""
WMS Mobile Racking TCP-IP Communication Streamlit App - Enhanced Version
WITH OFFICIAL WMS-DATA MAPPING - July 31, 2025
"""

import streamlit as st
import pandas as pd
import time
import struct
import os
import socket
import datetime
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List

# Import the enhanced parser with official mapping
from enhanced_response_parser import (
    parse_enhanced_mobile_response, 
    get_safety_assessment, 
    format_status_for_customer,
    decode_boolean_flags_byte5,
    decode_alarm_flags
)

# Page config
st.set_page_config(
    page_title="Stow WMS Official Controller",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        
        # Parse response with official mapping
        parsed_status = parse_enhanced_mobile_response(response)
        
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
        
        parsed_status = parse_enhanced_mobile_response(response)
        
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
    """Render enhanced gang control with official response analysis"""
    st.subheader("🎯 Gang Besturing (Officiële WMS-Data Mapping)")
    
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

def render_official_status_display():
    """Render status display with official WMS-Data interpretation"""
    st.subheader("📈 Officiële Status Analyse")
    
    if 'last_status' in st.session_state:
        status = st.session_state['last_status']
        
        # Safety assessment using official logic
        safety_color, safety_status, safety_advice = get_safety_assessment(status)
        
        # Main status display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Systeem Status", f"{safety_color} {safety_status}")
        
        with col2:
            sw_version = status.get('software_version', 'N/A')
            st.metric("Software Versie", f"{sw_version} ✅")
        
        with col3:
            power_status = "🟢 AAN" if status['operating_flags']['power_on'] else "🔴 UIT"
            st.metric("Voeding", power_status)
        
        with col4:
            timestamp = status.get('timestamp', 'N/A')
            st.metric("Laatste Update", timestamp)
        
        # Operating mode details
        st.subheader("⚙️ Bedrijfsmodus Details")
        ops_col1, ops_col2 = st.columns(2)
        
        with ops_col1:
            ops = status['operating_flags']
            st.write("**Verbinding & Controle:**")
            st.write(f"- TCP Verbinding: {'🟢 OK' if ops['tcp_connection_ok'] else '🔴 FOUT'}")
            st.write(f"- Automatische Modus: {'🟢 ACTIEF' if ops['auto_mode_active'] else '⚪ INACTIEF'}")
            st.write(f"- Handmatige Modus: {'🟢 ACTIEF' if ops['manual_mode_active'] else '⚪ INACTIEF'}")
            st.write(f"- Installatie Vrijgegeven: {'🟢 JA' if ops['installation_released'] else '🔴 NEE'}")
        
        with ops_col2:
            st.write("**Status & Beweging:**")
            st.write(f"- Voeding: {'🟢 AAN' if ops['power_on'] else '🔴 UIT'}")
            st.write(f"- Nachtmodus: {'🌙 ACTIEF' if ops['nightmode_active'] else '☀️ NORMAAL'}")
            st.write(f"- In Beweging: {'🟡 JA' if ops['installation_moving'] else '🟢 STILSTAND'}")
            st.write(f"- TCP Berichten: {status['tcp_received_messages']}")
        
        # Alarm status
        st.subheader("🚨 Alarm Monitor")
        active_alarms = [alarm for alarm, active in status['alarms'].items() if active]
        
        if active_alarms:
            st.error(f"❌ **{len(active_alarms)} ACTIEVE ALARMEN**")
            alarm_col1, alarm_col2 = st.columns(2)
            
            mid_point = len(active_alarms) // 2 + 1
            with alarm_col1:
                for alarm in active_alarms[:mid_point]:
                    st.write(f"🚨 {alarm.replace('_', ' ').title()}")
            
            with alarm_col2:
                for alarm in active_alarms[mid_point:]:
                    st.write(f"🚨 {alarm.replace('_', ' ').title()}")
        else:
            st.success("✅ **GEEN ACTIEVE ALARMEN**")
        
        # Gang lighting en control
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💡 Gang Verlichting")
            lit_aisles = [num for num, lit in status['aisle_lighting'].items() if lit]
            if lit_aisles:
                st.success(f"🟢 Verlichte Gangen: {', '.join(map(str, lit_aisles))}")
            else:
                st.info("⚪ Geen gangen verlicht")
        
        with col2:
            st.subheader("🎮 Gang Besturing")
            st.write(f"**Trolleys:** {status['trolley_count']}")
            st.write(f"**Vorkheftrucks:** {status['forklift_count']}")
            if status['aisle_to_open'] > 0:
                st.write(f"**Te Openen Gang:** {status['aisle_to_open']}")
            if status['last_open_aisle'] > 0:
                st.write(f"**Laatst Geopend:** {status['last_open_aisle']}")
        
        # Detailed technical info
        with st.expander("🔧 Technische Details", expanded=False):
            st.write("**Raw Response Data:**")
            st.code(f"Bytes: {status.get('raw_response', [])}")
            st.code(f"Hex: {status.get('hex_response', 'N/A')}")
            st.code(f"Words: {status.get('words', [])}")
            
            st.write("**Byte 5 Analyse (Officieel):**")
            byte5_val = status['raw_response'][5] if 'raw_response' in status else 0
            st.code(f"Byte 5 waarde: {byte5_val} (binair: {bin(byte5_val)})")
            
            for flag, value in status['operating_flags'].items():
                emoji = "✅" if value else "❌"
                st.write(f"  {emoji} {flag.replace('_', ' ').title()}: {value}")
        
        # Customer explanation
        with st.expander("📋 Klant Uitleg (Nederlands)", expanded=False):
            explanation = format_status_for_customer(status)
            st.markdown(explanation)
    
    else:
        st.info("Geen status data beschikbaar. Klik op 'STATUS AANVRAAG' om data op te halen.")

def render_test_with_real_data():
    """Test the parser with real RevPi data"""
    st.subheader("🧪 Test met Echte RevPi Data")
    
    if st.button("📊 Analyseer Echte RevPi Response"):
        # Real response: [0,2,2,5,9,9,0,0,223,27,0,0,0,0,0,0,0,14,0,0]
        real_response = bytes([0,2,2,5,9,9,0,0,223,27,0,0,0,0,0,0,0,14,0,0])
        
        parsed = parse_enhanced_mobile_response(real_response)
        
        st.success("✅ Echte data succesvol geanalyseerd!")
        
        # Show key findings
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Software Versie", parsed['software_version'] + " ✅")
        
        with col2:
            byte5_flags = parsed['operating_flags']
            active_flags = sum(1 for v in byte5_flags.values() if v)
            st.metric("Actieve Flags (Byte 5)", f"{active_flags}/7")
        
        with col3:
            safety_color, safety_status, _ = get_safety_assessment(parsed)
            st.metric("Safety Status", f"{safety_color} {safety_status}")
        
        # Store for display
        st.session_state['last_status'] = parsed
        
        st.info("💡 **Belangrijkste Bevinding:** Byte 5 = 9 betekent TCP OK + Manual Mode actief!")

# Main app layout
def main():
    st.title("🏭 Stow WMS Controller - Officiële Mapping")
    st.write("**Met officiële WMS-Data specificatie - 31 Juli 2025**")
    
    # Show the mystery solved banner
    st.success("🎉 **BYTE 5 MYSTERIE OPGELOST!** Byte 5 = 9 = TCP OK (bit 0) + Manual Mode (bit 3)")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Gang Besturing", 
        "📊 Status Analyse", 
        "🧪 Test Data",
        "📖 Documentatie"
    ])
    
    with tab1:
        render_enhanced_gang_control()
    
    with tab2:
        render_official_status_display()
    
    with tab3:
        render_test_with_real_data()
    
    with tab4:
        st.subheader("📖 Officiële WMS-Data Mapping")
        
        st.write("**Protocol Details:**")
        st.write("- **Legacy Protocol:** STX(0x02) + LEN + CMD(0x4F) + AISLE + CHECKSUM + ETX(0x03)")
        st.write("- **Simple Protocol:** [aisle_number, 1] voor opening, [0, 2] voor status")
        st.write("- **Response:** 20 bytes volgens officiële WMS-Data specificatie")
        
        st.write("**Opgeloste Mysteries:**")
        st.success("✅ Software versie: bytes 2-3 = [2,5] = v2.5")
        st.success("✅ Byte 5 waarde 9: TCP OK (bit 0) + Manual Mode (bit 3)")
        st.success("✅ Alarm bits: bytes 8-9 met alle PDS/emergency flags")
        st.success("✅ Gang verlichting: bytes 10-13 voor 32 gangen")
        
        st.info("**Volledige Mapping:** Zie `enhanced_response_parser.py` voor complete implementatie")

if __name__ == "__main__":
    main()
