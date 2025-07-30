import streamlit as st
import socket
import struct
import datetime
import time
from typing import Dict, Any

# Page config
st.set_page_config(page_title="Stow WMS Gang Besturing", layout="wide")

# Response parsing functie
def parse_mobile_racking_response(response_bytes: bytes) -> Dict[str, Any]:
    """Parse Mobile Racking 20-byte response"""
    if len(response_bytes) != 20:
        return {"error": f"Expected 20 bytes, got {len(response_bytes)}"}
    
    # Parse as 10 x 16-bit little-endian words
    words = struct.unpack('<10H', response_bytes)
    
    status = {
        'raw_response': list(response_bytes),
        'hex_response': response_bytes.hex().upper(),
        'words': list(words),
        'tcp_ip_connection': words[0] == 1,
        'system_status_word': words[1],
        'operation_mode_word': words[2], 
        'power_status': words[3] == 1,
        'mobile_data': words[4],
        'position_data': words[8],
        'ready_to_operate': words[1] > 0,
        'system_active': any(w > 0 for w in words[1:5]),
        'timestamp': datetime.datetime.now().strftime("%H:%M:%S")
    }
    
    return status
    
def explain_response_for_customer(status: Dict[str, Any]) -> str:
    """Create customer-friendly explanation of the 20-byte response"""
    
    explanations = []
    
    # Basic explanation
    explanations.append("🏭 **WAT BETEKENT DE MACHINE RESPONSE?**")
    explanations.append("=" * 50)
    explanations.append("")
    explanations.append("Elke keer als u een commando stuurt naar het mobiele stellingsysteem,")
    explanations.append("stuurt de machine een antwoord van 20 bytes terug. Dit antwoord vertelt")
    explanations.append("ons exact wat de status van het systeem is.")
    explanations.append("")
    
    # Simple status indicators
    explanations.append("📊 **EENVOUDIGE STATUS INDICATOREN:**")
    explanations.append("-" * 30)
    
    # Connection status
    if status.get('tcp_ip_connection', False):
        explanations.append("🟢 **Verbinding:** Machine is bereikbaar via netwerk")
    else:
        explanations.append("🔴 **Verbinding:** Machine reageert niet goed")
    
    # System active
    if status.get('system_active', False):
        explanations.append("🟢 **Systeem:** Machine is aan en operationeel")
    else:
        explanations.append("🔴 **Systeem:** Machine is uitgeschakeld of in storing")
    
    # Ready to operate
    if status.get('ready_to_operate', False):
        explanations.append("🟢 **Klaar voor gebruik:** Machine kan commando's ontvangen")
    else:
        explanations.append("🔴 **Niet klaar:** Machine kan nu geen commando's uitvoeren")
    
    # Power status
    if status.get('power_status', False):
        explanations.append("🟢 **Voeding:** Stroomvoorziening is in orde")
    else:
        explanations.append("🔴 **Voeding:** Probleem met stroomvoorziening")
    
    explanations.append("")
    
    # Detailed data explanation
    explanations.append("🔍 **GEDETAILLEERDE INFORMATIE:**")
    explanations.append("-" * 25)
    explanations.append(f"• **Systeem Status Nummer:** {status.get('system_status_word', 'N/A')}")
    explanations.append("  (Hoe hoger dit getal, hoe actiever het systeem)")
    explanations.append("")
    explanations.append(f"• **Operatie Modus:** {status.get('operation_mode_word', 'N/A')}")
    explanations.append("  (Welke bedrijfsmodus de machine gebruikt)")
    explanations.append("")
    explanations.append(f"• **Positie Informatie:** {status.get('position_data', 'N/A')}")
    explanations.append("  (Huidige positie van de stellingonderdelen)")
    explanations.append("")
    explanations.append(f"• **Mobiele Data:** {status.get('mobile_data', 'N/A')}")
    explanations.append("  (Specifieke informatie over bewegende delen)")
    explanations.append("")
    
    # Real-world examples
    explanations.append("💡 **PRAKTISCHE VOORBEELDEN:**")
    explanations.append("-" * 20)
    explanations.append("")
    explanations.append("**Scenario 1 - Alles werkt perfect:**")
    explanations.append("• Alle lampjes zijn groen 🟢")
    explanations.append("• Systeem Status: 1282 (hoog getal = actief)")
    explanations.append("• ➜ U kunt veilig gangen openen")
    explanations.append("")
    explanations.append("**Scenario 2 - Machine is uitgeschakeld:**")
    explanations.append("• Alle waardes zijn 0")
    explanations.append("• Systeem Status: 0")
    explanations.append("• ➜ Machine moet eerst aangezet worden")
    explanations.append("")
    explanations.append("**Scenario 3 - Machine heeft storing:**")
    explanations.append("• Sommige lampjes rood 🔴")
    explanations.append("• Systeem Status: laag getal")
    explanations.append("• ➜ Technicus moet systeem controleren")
    explanations.append("")
    
    # Safety information
    explanations.append("⚠️ **VEILIGHEID:**")
    explanations.append("-" * 15)
    explanations.append("• Gebruik alleen gang commando's als alle lampjes groen zijn")
    explanations.append("• Bij rode lampjes: stop met gebruiken en bel onderhoud")
    explanations.append("• Bij twijfel: gebruik 'STATUS AANVRAAG' voor actuele informatie")
    explanations.append("")
    
    # Technical reference (simple)
    explanations.append("🔧 **VOOR DE TECHNICUS:**")
    explanations.append("-" * 20)
    explanations.append(f"• Raw Response: {status.get('raw_response', 'N/A')}")
    explanations.append(f"• Hex Format: {status.get('hex_response', 'N/A')}")
    explanations.append(f"• Laatste Update: {status.get('timestamp', 'N/A')}")
    
    return "\n".join(explanations)

def get_status_summary(status: Dict[str, Any]) -> str:
    """Get a simple one-line status summary"""
    if not status:
        return "❓ Geen status beschikbaar"
    
    if status.get('system_active', False) and status.get('ready_to_operate', False):
        return "🟢 SYSTEEM OPERATIONEEL - Klaar voor gebruik"
    elif status.get('system_active', False):
        return "🟡 SYSTEEM ACTIEF - Beperkt beschikbaar"
    else:
        return "🔴 SYSTEEM INACTIEF - Niet beschikbaar"

def send_aisle_command(aisle_number: int, plc_ip: str = "1.1.1.2", plc_port: int = 2000, use_legacy_protocol: bool = True):
    """Send aisle command and get response"""
    try:
        # Connect to PLC
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((plc_ip, plc_port))
        
        if use_legacy_protocol:
            # Legacy WMS Protocol: STX + LEN + CMD + AISLE + CHK + ETX
            start_byte = 0x02
            length = 2
            command = 0x4F  # 'O' for Open
            aisle_byte = aisle_number
            checksum = length ^ command ^ aisle_byte
            end_byte = 0x03
            
            command_bytes = bytes([start_byte, length, command, aisle_byte, checksum, end_byte])
        else:
            # Simple 2-byte protocol: [aisle_number, 1]
            command_bytes = bytes([aisle_number, 1])
        
        # Send command
        sock.send(command_bytes)
        
        # Wait for response
        response = sock.recv(20)  # Expect 20-byte response
        sock.close()
        
        return {"success": True, "response": response, "command_sent": command_bytes}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_status_request(plc_ip: str = "1.1.1.2", plc_port: int = 2000):
    """Send status request and get response"""
    try:
        # Connect to PLC
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((plc_ip, plc_port))
        
        # Status request: [0, 2]
        command_bytes = bytes([0, 2])
        
        # Send command
        sock.send(command_bytes)
        
        # Wait for response
        response = sock.recv(20)  # Expect 20-byte response
        sock.close()
        
        return {"success": True, "response": response, "command_sent": command_bytes}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Initialize session state for machine status
if 'machine_status' not in st.session_state:
    st.session_state.machine_status = None
if 'last_response_time' not in st.session_state:
    st.session_state.last_response_time = None
if 'use_legacy_protocol' not in st.session_state:
    st.session_state.use_legacy_protocol = True

# Header
st.title("🎯 Stow WMS Gang Besturing")
st.markdown("**Revolution Pi Connect SE - Gang Commando Interface**")

# Direct gang besturing - GEEN TABS, GEEN SIDEBAR
st.header("Gang Besturing Commando's")

# Protocol selector
protocol_col1, protocol_col2 = st.columns([3, 1])

with protocol_col1:
    st.markdown("**Protocol Selectie:**")
    protocol_option = st.radio(
        "Kies protocol format:",
        ["Legacy WMS (6 bytes)", "Simple Protocol (2 bytes)"],
        index=0 if st.session_state.use_legacy_protocol else 1,
        horizontal=True
    )
    st.session_state.use_legacy_protocol = protocol_option.startswith("Legacy")

with protocol_col2:
    st.markdown("**Protocol Info:**")
    if st.session_state.use_legacy_protocol:
        st.code("STX+LEN+CMD+AISLE+CHK+ETX")
    else:
        st.code("[AISLE, 1] of [0, 2]")

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Gang Selectie")
    
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
    st.markdown("**Alternatief: Gebruik slider**")
    aisle_slider = st.slider("Gang Selectie", 1, 24, int(aisle_number))
    
    # Use slider value if different
    if aisle_slider != aisle_number:
        aisle_number = aisle_slider
    
    # WMS Protocol generatie
    st.markdown("---")
    st.subheader("🔧 WMS Protocol Commando")
    
    if st.session_state.use_legacy_protocol:
        # Legacy protocol: STX + LEN + CMD + AISLE + CHK + ETX
        start_byte = 0x02
        length = 2
        command = 0x4F  # 'O' for Open
        aisle_byte = aisle_number
        checksum = length ^ command ^ aisle_byte
        end_byte = 0x03
        
        command_bytes = [start_byte, length, command, aisle_byte, checksum, end_byte]
        hex_string = ' '.join([f'{b:02X}' for b in command_bytes])
        
        # Show protocol details
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.code(f"""
Gang {aisle_number} Commando (Legacy):
TCP/IP Bytes: {hex_string}

Protocol Breakdown:
STX: 0x{start_byte:02X} (Start)
LEN: 0x{length:02X} (Length)
CMD: 0x{command:02X} ('O' Open)
GANG: 0x{aisle_byte:02X} ({aisle_number})
CHK: 0x{checksum:02X} (XOR)
ETX: 0x{end_byte:02X} (End)
            """)
        
        with col_b:
            st.info(f"""
**Target:** Gang {aisle_number}
**Actie:** Open Gang
**Protocol:** Legacy WMS TCP/IP
**Bytes:** {len(command_bytes)} bytes
**Checksum:** Geldig
            """)
    else:
        # Simple protocol: [aisle_number, 1]
        command_bytes = [aisle_number, 1]
        hex_string = ' '.join([f'{b:02X}' for b in command_bytes])
        
        # Show protocol details
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.code(f"""
Gang {aisle_number} Commando (Simple):
TCP/IP Bytes: {hex_string}

Protocol Breakdown:
AISLE: 0x{aisle_number:02X} ({aisle_number})
CMD: 0x01 (Open)
            """)
        
        with col_b:
            st.info(f"""
**Target:** Gang {aisle_number}
**Actie:** Open Gang
**Protocol:** Simple TCP/IP
**Bytes:** {len(command_bytes)} bytes
**Format:** [AISLE, 1]
            """)
    
    # Status request preview
    st.markdown("**Status Request Preview:**")
    if st.session_state.use_legacy_protocol:
        status_bytes = [0x02, 0x01, 0x53, 0x00, 0x52, 0x03]  # Example status request
        status_hex = ' '.join([f'{b:02X}' for b in status_bytes])
        st.code(f"Status Request (Legacy): {status_hex}")
    else:
        status_bytes = [0, 2]
        status_hex = ' '.join([f'{b:02X}' for b in status_bytes])
        st.code(f"Status Request (Simple): {status_hex}")
    st.markdown("---")
    st.subheader("🚀 Commando Verzending")
    
    col_send1, col_send2 = st.columns(2)
    
    with col_send1:
        if st.button(f"✅ OPEN GANG {aisle_number}", type="primary", use_container_width=True):
            with st.spinner(f"📡 Commando wordt verzonden naar gang {aisle_number}..."):
                result = send_aisle_command(aisle_number, "1.1.1.2", 2000, st.session_state.use_legacy_protocol)
                
                if result["success"]:
                    st.success(f"🎉 Commando verzonden naar gang {aisle_number}!")
                    st.balloons()
                    
                    # Parse response
                    status = parse_mobile_racking_response(result["response"])
                    st.session_state.machine_status = status
                    st.session_state.last_response_time = datetime.datetime.now()
                    
                    st.success(f"📤 Command bytes verzonden: {result['command_sent'].hex().upper()}")
                    st.success(f"📥 Response ontvangen: {len(result['response'])} bytes")
                    st.success(f"✅ Gang {aisle_number} opening geïnitieerd!")
                    
                else:
                    st.error(f"❌ Fout bij verzenden: {result['error']}")
                    st.info("💡 Tip: Controleer of de PLC bereikbaar is via netwerk instellingen")
    
    with col_send2:
        if st.button(f"🧪 TEST GANG {aisle_number}", use_container_width=True):
            # Show what would be sent
            protocol_type = "Legacy WMS" if st.session_state.use_legacy_protocol else "Simple"
            st.info(f"🔍 {protocol_type} commando voor gang {aisle_number} is geldig!")
            if st.session_state.use_legacy_protocol:
                test_bytes = [0x02, 0x02, 0x4F, aisle_number, 0x02 ^ 0x4F ^ aisle_number, 0x03]
            else:
                test_bytes = [aisle_number, 1]
            test_hex = ' '.join([f'{b:02X}' for b in test_bytes])
            st.info(f"📋 Hex bytes: {test_hex}")
            st.success("✅ Test geslaagd - commando is correct geformatteerd!")
            
        # Status refresh button
        if st.button("🔄 STATUS AANVRAAG", use_container_width=True):
            with st.spinner("📡 Status wordt opgehaald..."):
                if st.session_state.use_legacy_protocol:
                    # For legacy, use a dummy gang command to get status
                    result = send_aisle_command(1, "1.1.1.2", 2000, True)
                else:
                    # Use dedicated status request
                    result = send_status_request("1.1.1.2", 2000)
                
                if result["success"]:
                    status = parse_mobile_racking_response(result["response"])
                    st.session_state.machine_status = status
                    st.session_state.last_response_time = datetime.datetime.now()
                    st.success("✅ Status bijgewerkt!")
                    st.info(f"📤 Status request: {result['command_sent'].hex().upper()}")
                else:
                    st.error(f"❌ Status ophalen mislukt: {result['error']}")

with col2:
    st.subheader("⚡ Quick Access")
    
    # Quick gang buttons
    quick_aisles = [1, 5, 10, 15, 20, 24]
    
    st.markdown("**Veelgebruikte Gangen:**")
    for aisle in quick_aisles:
        if st.button(f"Gang {aisle}", key=f"quick_{aisle}", use_container_width=True):
            with st.spinner(f"📡 Gang {aisle} wordt geopend..."):
                result = send_aisle_command(aisle, "1.1.1.2", 2000, st.session_state.use_legacy_protocol)
                
                if result["success"]:
                    st.success(f"✅ Gang {aisle} geopend!")
                    status = parse_mobile_racking_response(result["response"])
                    st.session_state.machine_status = status
                    st.session_state.last_response_time = datetime.datetime.now()
                else:
                    st.error(f"❌ Gang {aisle} fout: {result['error']}")
    
    st.markdown("---")
    st.subheader("📊 Status")
    
    current_time = datetime.datetime.now()
    st.metric("Tijd", current_time.strftime("%H:%M:%S"))
    st.metric("Actieve Gang", aisle_number)
    st.metric("Protocol", "WMS TCP/IP")
    
    # Machine status indicator
    if st.session_state.machine_status:
        status = st.session_state.machine_status
        if status.get('system_active', False):
            st.metric("Machine Status", "🟢 ACTIEF")
        else:
            st.metric("Machine Status", "🔴 INACTIEF")
    else:
        st.metric("Machine Status", "❓ ONBEKEND")
    
    st.markdown("---")
    st.subheader("🌐 Netwerk")
    st.text("RevPi: 192.168.0.12")
    st.text("PLC: 1.1.1.2:2000")

# Machine Status Section
if st.session_state.machine_status:
    st.markdown("---")
    st.header("🏭 Machine Status Dashboard")
    
    status = st.session_state.machine_status
    
    # Simple status summary first
    status_summary = get_status_summary(status)
    st.markdown(f"### {status_summary}")
    st.markdown("")
    
    # Status overview row
    col_status1, col_status2, col_status3, col_status4 = st.columns(4)
    
    with col_status1:
        connection_color = "🟢" if status.get('tcp_ip_connection', False) else "🔴"
        st.metric("TCP Verbinding", f"{connection_color} {'OK' if status.get('tcp_ip_connection', False) else 'FOUT'}")
    
    with col_status2:
        active_color = "🟢" if status.get('system_active', False) else "🔴"
        st.metric("Systeem", f"{active_color} {'ACTIEF' if status.get('system_active', False) else 'INACTIEF'}")
    
    with col_status3:
        ready_color = "🟢" if status.get('ready_to_operate', False) else "🔴"
        st.metric("Operationeel", f"{ready_color} {'JA' if status.get('ready_to_operate', False) else 'NEE'}")
    
    with col_status4:
        power_color = "🟢" if status.get('power_status', False) else "🔴"
        st.metric("Voeding", f"{power_color} {'OK' if status.get('power_status', False) else 'FOUT'}")
    
    # Customer explanation section
    st.markdown("---")
    st.header("📖 Wat betekent deze informatie?")
    
    # Toggle for detailed explanation
    show_explanation = st.checkbox("🔍 Toon gedetailleerde uitleg (voor klanten)", value=False)
    
    if show_explanation:
        explanation = explain_response_for_customer(status)
        st.markdown(explanation)
    else:
        # Brief summary
        st.info(f"""
        **🎯 Korte samenvatting:**
        
        De machine stuurt elke keer een antwoord van 20 bytes terug als u een commando geeft.
        Dit antwoord vertelt ons of het systeem klaar is voor gebruik.
        
        **Huidige status:** {get_status_summary(status)}
        
        **Veiligheidsadvies:** {'✅ Veilig om gangen te openen' if status.get('system_active', False) and status.get('ready_to_operate', False) else '⚠️ Controleer systeem voordat u verdergaat'}
        
        *(Vink het vakje hierboven aan voor een uitgebreide uitleg)*
        """)
    
    # Technical details (collapsible)
    with st.expander("🔧 Technische Details (voor specialisten)"):
        col_detail1, col_detail2 = st.columns(2)
        
        with col_detail1:
            st.subheader("📋 Systeem Details")
            st.code(f"""
Systeem Status: {status.get('system_status_word', 'N/A')}
Operatie Modus: {status.get('operation_mode_word', 'N/A')}
Mobile Data: {status.get('mobile_data', 'N/A')}
Positie Data: {status.get('position_data', 'N/A')}

Laatste Update: {status.get('timestamp', 'N/A')}
            """)
        
        with col_detail2:
            st.subheader("🔍 Raw Response Data")
            st.code(f"""
HEX: {status.get('hex_response', 'N/A')}
Words: {status.get('words', 'N/A')}
Raw Bytes: {status.get('raw_response', 'N/A')}

Response Lengte: 20 bytes
Format: 10x 16-bit woorden
            """)
    
    # Example responses section
    with st.expander("💡 Voorbeeld Responses (voor training)"):
        st.markdown("""
        **🟢 Voorbeeld 1 - Perfect werkend systeem:**
        ```
        Response: [0, 0, 2, 5, 2, 2, 0, 0, 223, 27, 0, 0, 0, 0, 0, 0, 0, 14, 0, 0]
        Betekenis: Systeem is actief (status: 1282), klaar voor commando's
        Actie: ✅ Veilig om gangen te openen
        ```
        
        **🔴 Voorbeeld 2 - Uitgeschakeld systeem:**
        ```
        Response: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        Betekenis: Alle waardes zijn 0, systeem reageert niet
        Actie: ❌ Machine moet eerst aangezet worden
        ```
        
        **🟡 Voorbeeld 3 - Systeem in storing:**
        ```
        Response: [0, 0, 1, 0, 0, 0, 0, 0, 50, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        Betekenis: Lage waardes, systeem heeft probleem
        Actie: ⚠️ Technicus raadplegen
        ```
        """)
    
    # Last response time
    if st.session_state.last_response_time:
        time_diff = datetime.datetime.now() - st.session_state.last_response_time
        st.info(f"⏰ Laatste response: {time_diff.seconds} seconden geleden")
        
        if time_diff.seconds > 30:
            st.warning("⚠️ Status data is mogelijk verouderd. Klik 'STATUS AANVRAAG' voor recente gegevens.")

else:
    st.markdown("---")
    st.info("""
    📊 **Machine Status:** Geen status data beschikbaar. 
    
    **Wat betekent dit?**
    De machine heeft nog geen antwoord gestuurd. Dit kan betekenen:
    • Nog geen commando verzonden
    • Machine is niet bereikbaar
    • Netwerk probleem
    
    **Wat kunt u doen?**
    • Klik 'STATUS AANVRAAG' om de huidige status op te halen
    • Controleer of de machine aangesloten is
    • Voer een gang commando uit om status te krijgen
    """)

# Connection settings onderaan
st.markdown("---")
st.header("⚙️ Connection Settings")

col_net1, col_net2, col_net3 = st.columns(3)

with col_net1:
    plc_ip = st.text_input("PLC IP Address", value="1.1.1.2")

with col_net2:
    plc_port = st.number_input("PLC Port", value=2000, min_value=1, max_value=65535)

with col_net3:
    if st.button("🔗 Test PLC Verbinding", type="secondary"):
        with st.spinner("Testing verbinding..."):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((plc_ip, plc_port))
                sock.close()
                
                if result == 0:
                    st.success(f"✅ Verbonden met {plc_ip}:{plc_port}")
                else:
                    st.error(f"❌ Verbinding mislukt naar {plc_ip}:{plc_port}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# System info
st.markdown("---")
st.info("🏭 **Revolution Pi Connect SE** | WMS Mobile Racking Controller | Gang Besturing Interface")
st.text("✅ Alle gang besturing functionaliteit is direct beschikbaar zonder tabs/navigatie")

# Documentation section
st.markdown("---")
st.header("📚 Documentatie & Uitleg")

doc_col1, doc_col2, doc_col3 = st.columns(3)

with doc_col1:
    if st.button("📋 Response Documentatie", use_container_width=True):
        st.info("📄 Volledige technische documentatie beschikbaar in: WMS_Response_Documentation.md")

with doc_col2:
    if st.button("📧 Klant Email Voorbeeld", use_container_width=True):
        st.info("✉️ Klant-vriendelijke uitleg beschikbaar in: Customer_Response_Email.txt")

with doc_col3:
    if st.button("🔍 Response Analyzer", use_container_width=True):
        st.info("🛠️ Gebruik de 'STATUS AANVRAAG' functie hierboven voor live analyse")

# Quick reference
with st.expander("📖 Snelle Referentie - 20-Byte Response"):
    st.markdown("""
    ### 🎯 **Wat zijn de 20 bytes?**
    
    **Structuur**: 10 woorden van elk 2 bytes
    ```
    [Word0] [Word1] [Word2] [Word3] [Word4] [Word5] [Word6] [Word7] [Word8] [Word9]
     0-1     2-3     4-5     6-7     8-9    10-11   12-13   14-15   16-17   18-19
    ```
    
    ### 📊 **Belangrijkste Velden**:
    
    **Word 0 (Bytes 0-1)**: TCP Verbinding
    - `0` = Normaal (voor dit systeem)
    - `1` = Verbinding bevestigd
    
    **Word 1 (Bytes 2-3)**: Systeem Status ⭐ BELANGRIJKSTE
    - `1282` = Perfect werkend systeem
    - `0` = Systeem uitgeschakeld  
    - `1-100` = Storing of probleem
    
    **Word 2 (Bytes 4-5)**: Software Versie
    - `514` = Versie 2.2
    - `258` = Versie 1.2
    
    **Word 4 (Bytes 8-9)**: Mobile Data
    - `7135` = Actieve beweging
    - `0` = Geen beweging
    
    **Word 8 (Bytes 16-17)**: Positie Data  
    - `3584` = Operationele positie
    - `0` = Standaard positie
    
    ### 🚦 **Kleur Codes**:
    - 🟢 **Groen**: Systeem Status > 1000
    - 🟡 **Geel**: Systeem Status 100-1000  
    - 🔴 **Rood**: Systeem Status < 100 of 0
    
    ### ⚠️ **Veiligheidsregel**:
    **Alleen bij groene status gangen openen!**
    """)

# WMS-Data field mapping
with st.expander("🗺️ WMS-Data Veld Mapping (volgens specificatie)"):
    st.markdown("""
    ### 📋 **Veld Correspondentie**:
    
    | Offset | Veld Naam | Response Positie | Normale Waarde |
    |--------|-----------|------------------|-----------------|
    | **0.0** | Command Request | Word 1 | 1-19 |
    | **1.0** | Start Operation | Word 1 | true/false |
    | **1.1** | Request Status | Word 1 | false |
    | **2.0** | Software Major | Word 2 | 2 |
    | **3.0** | Software Minor | Word 2 | 2-5 |
    | **4.0** | TCP-IP Received | Word 3 | 16#0 |
    | **5.0** | TCP-IP Connection | Word 0 | true |
    | **5.1** | Automatic Mode | Status bits | false |
    | **5.2** | Mobiles Released | Status bits | false |
    | **5.3** | Manual Mode | Status bits | false |
    | **5.4** | Night Mode | Status bits | false |
    | **5.5** | Mobiles Moving | Word 4 | false/true |
    | **5.6** | Power ON | Word 3 | false |
    | **6.0** | Mobile Identity | Word 4 | 16#0 |
    | **7.0** | Liftrack Inside | Word 8 | 16#0 |
    | **8.0-9.4** | Alarm Fields | Various | false (geen alarm) |
    | **10.0** | Lighting Aisles | Word X | 16#0 |
    | **14.0** | Selected Aisle | Word X | 16#0 |
    
    ### 🔧 **Alarm Velden (8.0-9.4)**:
    - **8.0**: Lichtgordijn voorkant
    - **8.1**: Lichtgordijn achterkant  
    - **8.2**: Lichtgordijn zijkant
    - **8.3**: Noodstop alarm
    - **8.4**: Aandrijving alarm
    - **8.5-8.6**: Lichtstraal alarmen
    - **8.7-9.4**: Aanvullende veiligheidsalarmen
    
    **Alle alarm velden**: `false` = Normaal, `true` = Alarm actief
    """)

st.markdown("---")
