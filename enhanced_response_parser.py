#!/usr/bin/env python3
"""
Enhanced Mobile Racking Response Parser with Official WMS-Data Mapping
Based on official STOW documentation provided 31 July 2025
"""

import struct
import datetime
from typing import Dict, Any, List, Tuple

def decode_boolean_flags_byte5(byte_value: int) -> Dict[str, bool]:
    """
    Decode byte 5 Boolean flags according to official WMS-Data specification
    
    Offset 5.0-5.6 are packed as bits in byte 5:
    - Bit 0 (5.0): TCP-IP connection status
    - Bit 1 (5.1): Operating mode AUTO active  
    - Bit 2 (5.2): Installation released
    - Bit 3 (5.3): Operating mode MANUAL active
    - Bit 4 (5.4): Nightmode active
    - Bit 5 (5.5): Installation moving
    - Bit 6 (5.6): Power ON
    - Bit 7: Reserved
    """
    return {
        'tcp_connection_ok': bool(byte_value & 0x01),      # Bit 0
        'auto_mode_active': bool(byte_value & 0x02),       # Bit 1  
        'installation_released': bool(byte_value & 0x04),  # Bit 2
        'manual_mode_active': bool(byte_value & 0x08),     # Bit 3
        'nightmode_active': bool(byte_value & 0x10),       # Bit 4
        'installation_moving': bool(byte_value & 0x20),    # Bit 5
        'power_on': bool(byte_value & 0x40),               # Bit 6
        'reserved_bit7': bool(byte_value & 0x80)           # Bit 7
    }

def decode_alarm_flags(byte8: int, byte9: int) -> Dict[str, bool]:
    """
    Decode alarm flags from bytes 8-9 (offset 8.0-9.4)
    """
    alarms = {}
    
    # Byte 8 alarms (offset 8.0-8.7)
    alarms['pds_front_interrupted'] = bool(byte8 & 0x01)      # 8.0
    alarms['pds_back_interrupted'] = bool(byte8 & 0x02)       # 8.1
    alarms['pds_side_interrupted'] = bool(byte8 & 0x04)       # 8.2
    alarms['emergency_shutdown'] = bool(byte8 & 0x08)         # 8.3
    alarms['underdrive_sensor_detection'] = bool(byte8 & 0x10) # 8.4
    alarms['fds_sensor_issue'] = bool(byte8 & 0x20)           # 8.5
    alarms['pallet_detection_master'] = bool(byte8 & 0x40)    # 8.6
    alarms['50k1_relay_off'] = bool(byte8 & 0x80)             # 8.7
    
    # Byte 9 alarms (offset 9.0-9.4, only first 5 bits used)
    alarms['emergency_button_slave'] = bool(byte9 & 0x01)     # 9.0
    alarms['underdrive_sensor_slave'] = bool(byte9 & 0x02)    # 9.1
    alarms['pd_slave_not_ok'] = bool(byte9 & 0x04)            # 9.2
    alarms['50k2_relay_off'] = bool(byte9 & 0x08)             # 9.3
    alarms['pallet_detection_slave'] = bool(byte9 & 0x10)     # 9.4
    
    return alarms

def decode_aisle_lighting(bytes_10_13: List[int]) -> Dict[int, bool]:
    """
    Decode aisle lighting status from bytes 10-13 (offsets 10.0-13.7)
    32 aisles total as Boolean flags
    """
    lighting = {}
    aisle_num = 1
    
    for byte_idx, byte_val in enumerate(bytes_10_13):
        for bit in range(8):
            if aisle_num <= 32:
                lighting[aisle_num] = bool(byte_val & (1 << bit))
                aisle_num += 1
    
    return lighting

def parse_enhanced_mobile_response(response_bytes: bytes) -> Dict[str, Any]:
    """
    Parse 20-byte Mobile Racking response with official WMS-Data mapping
    
    Args:
        response_bytes: 20-byte response from Mobile Racking system
        
    Returns:
        Dict with complete parsed status information
    """
    if len(response_bytes) != 20:
        raise ValueError(f"Expected 20 bytes, got {len(response_bytes)}")
    
    # Convert to list for easy access
    bytes_list = list(response_bytes)
    
    # Parse as 10 x 16-bit little-endian words
    words = struct.unpack('<10H', response_bytes)
    
    # Create comprehensive status dictionary
    status = {
        'raw_response': bytes_list,
        'hex_response': response_bytes.hex().upper(),
        'words': list(words),
        'timestamp': datetime.datetime.now().strftime("%H:%M:%S"),
        
        # Word 0 (Bytes 0-1): Command & Start flags
        'command_request': bytes_list[0],  # Offset 0.0 (1-19)
        'start_opening': bool(bytes_list[1] & 0x01),  # Offset 1.0
        'request_status': bool(bytes_list[1] & 0x02), # Offset 1.1
        
        # Word 1 (Bytes 2-3): Software Version ✅ CONFIRMED
        'software_major': bytes_list[2],   # Offset 2.0
        'software_minor': bytes_list[3],   # Offset 3.0
        'software_version': f"{bytes_list[2]}.{bytes_list[3]}",
        
        # Word 2 (Bytes 4-5): TCP & Operating modes
        'tcp_received_messages': bytes_list[4],  # Offset 4.0
        'operating_flags': decode_boolean_flags_byte5(bytes_list[5]), # Offset 5.0-5.6
        
        # Word 3 (Bytes 6-7): Trolley & Forklift counts
        'trolley_count': bytes_list[6],    # Offset 6.0
        'forklift_count': bytes_list[7],   # Offset 7.0
        
        # Word 4 (Bytes 8-9): Alarm flags
        'alarms': decode_alarm_flags(bytes_list[8], bytes_list[9]),
        
        # Words 5-6 (Bytes 10-13): Aisle lighting
        'aisle_lighting': decode_aisle_lighting(bytes_list[10:14]),
        
        # Word 7 (Bytes 14-15): Aisle control
        'aisle_to_open': bytes_list[14],   # Offset 14.0
        'last_open_aisle': bytes_list[15], # Offset 15.0
        
        # Word 8 (Bytes 16-17): MCC Errors
        'mcc_error_trolley': bytes_list[16], # Offset 16.0
        'mcc_error_code': bytes_list[17],    # Offset 17.0
        
        # Word 9 (Bytes 18-19): Trolley Errors  
        'trolley_error_number': bytes_list[18], # Offset 18.0
        'trolley_error_code': bytes_list[19],   # Offset 19.0
    }
    
    # Add derived health indicators
    status['system_healthy'] = not any(status['alarms'].values())
    status['any_aisle_lit'] = any(status['aisle_lighting'].values())
    status['power_status'] = status['operating_flags']['power_on']
    status['connection_ok'] = status['operating_flags']['tcp_connection_ok']
    status['installation_ready'] = (
        status['operating_flags']['installation_released'] and 
        status['operating_flags']['power_on']
    )
    
    return status

def get_safety_assessment(status: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Get safety assessment based on parsed status
    
    Returns:
        Tuple of (color_code, status_text, advice)
    """
    # Check for any active alarms
    active_alarms = [alarm for alarm, active in status['alarms'].items() if active]
    
    if active_alarms:
        return ("🔴", "ALARM ACTIEF", f"Stop gebruik - Actieve alarmen: {', '.join(active_alarms)}")
    
    elif not status['operating_flags']['power_on']:
        return ("⚫", "UITGESCHAKELD", "Machine is uitgeschakeld - schakel voeding in")
    
    elif not status['operating_flags']['installation_released']:
        return ("🟡", "NIET VRIJGEGEVEN", "Installatie nog niet vrijgegeven voor gebruik")
    
    elif status['operating_flags']['installation_moving']:
        return ("🟡", "IN BEWEGING", "Wacht tot beweging voltooid is")
    
    elif status['installation_ready']:
        return ("🟢", "KLAAR VOOR GEBRUIK", "Veilig om gang commando's te sturen")
    
    else:
        return ("🟡", "BEPERKT KLAAR", "Controleer status voordat u doorgaat")

def format_status_for_customer(status: Dict[str, Any]) -> str:
    """
    Format complete status in customer-friendly Dutch
    """
    safety_color, safety_status, safety_advice = get_safety_assessment(status)
    
    lines = []
    lines.append(f"# 🏭 STOW Mobile Racking Status")
    lines.append(f"")
    lines.append(f"**Status:** {safety_color} **{safety_status}**")
    lines.append(f"**Advies:** {safety_advice}")
    lines.append(f"")
    
    # Software info
    lines.append(f"## 💻 Systeem Informatie")
    lines.append(f"- **Software Versie:** {status['software_version']} ✅")
    lines.append(f"- **Laatst Bijgewerkt:** {status['timestamp']}")
    lines.append(f"")
    
    # Operating modes
    ops = status['operating_flags']
    lines.append(f"## ⚙️ Bedrijfsmodus")
    lines.append(f"- **Voeding:** {'🟢 AAN' if ops['power_on'] else '🔴 UIT'}")
    lines.append(f"- **Verbinding:** {'🟢 OK' if ops['tcp_connection_ok'] else '🔴 FOUT'}")
    lines.append(f"- **Auto Modus:** {'🟢 ACTIEF' if ops['auto_mode_active'] else '⚪ INACTIEF'}")
    lines.append(f"- **Handmatige Modus:** {'🟢 ACTIEF' if ops['manual_mode_active'] else '⚪ INACTIEF'}")
    lines.append(f"- **Installatie Vrijgegeven:** {'🟢 JA' if ops['installation_released'] else '🔴 NEE'}")
    lines.append(f"- **In Beweging:** {'🟡 JA' if ops['installation_moving'] else '🟢 NEE'}")
    lines.append(f"")
    
    # Alarm status
    active_alarms = [alarm for alarm, active in status['alarms'].items() if active]
    lines.append(f"## 🚨 Alarm Status")
    if active_alarms:
        lines.append(f"❌ **ALARMEN ACTIEF:** {len(active_alarms)}")
        for alarm in active_alarms[:5]:  # Show max 5
            lines.append(f"  - {alarm.replace('_', ' ').title()}")
    else:
        lines.append(f"✅ **GEEN ACTIEVE ALARMEN**")
    lines.append(f"")
    
    # Gang lighting
    lit_aisles = [num for num, lit in status['aisle_lighting'].items() if lit]
    lines.append(f"## 💡 Gang Verlichting")
    if lit_aisles:
        lines.append(f"🟢 **Verlichte Gangen:** {', '.join(map(str, lit_aisles))}")
    else:
        lines.append(f"⚪ **Geen gangen verlicht**")
    lines.append(f"")
    
    # Control info
    lines.append(f"## 🎮 Besturing")
    lines.append(f"- **Trolleys in Installatie:** {status['trolley_count']}")
    lines.append(f"- **Vorkheftrucks Binnen:** {status['forklift_count']}")
    if status['aisle_to_open'] > 0:
        lines.append(f"- **Gang om te Openen:** {status['aisle_to_open']}")
    if status['last_open_aisle'] > 0:
        lines.append(f"- **Laatst Geopende Gang:** {status['last_open_aisle']}")
    
    return "\\n".join(lines)

# Test function for the actual RevPi response
def test_with_real_data():
    """Test with the real RevPi response data"""
    # Real response: [0,2,2,5,9,9,0,0,223,27,0,0,0,0,0,0,0,14,0,0]
    real_response = bytes([0,2,2,5,9,9,0,0,223,27,0,0,0,0,0,0,0,14,0,0])
    
    parsed = parse_enhanced_mobile_response(real_response)
    
    print("🔍 ANALYSE VAN ECHTE REVPI DATA:")
    print("=" * 40)
    print(f"Software Versie: {parsed['software_version']} ✅")
    print(f"Byte 5 waarde: {real_response[5]} (binair: {bin(real_response[5])})")
    print("")
    print("Boolean Flags in Byte 5:")
    for flag, value in parsed['operating_flags'].items():
        print(f"  {flag}: {value}")
    print("")
    print("Safety Assessment:")
    color, status, advice = get_safety_assessment(parsed)
    print(f"  Status: {color} {status}")
    print(f"  Advies: {advice}")
    
    return parsed

if __name__ == "__main__":
    test_with_real_data()
