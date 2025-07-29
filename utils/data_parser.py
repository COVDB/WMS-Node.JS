"""
Data parsing utilities voor WMS systeem
"""

import struct
from typing import Dict, Any, List
from datetime import datetime

def format_hex_data(data: bytes) -> str:
    """
    Format bytes data als hex string voor debugging
    
    Args:
        data (bytes): Raw bytes data
        
    Returns:
        str: Geformatteerde hex string
    """
    return ' '.join(f'{b:02X}' for b in data)

def parse_lighting_rules(dword_value: int) -> List[int]:
    """
    Parse lighting rules DWORD naar lijst van aisle nummers
    
    Args:
        dword_value (int): 32-bit DWORD waarde
        
    Returns:
        List[int]: Lijst van aisle nummers die aan zijn (1-32)
    """
    aisles = []
    for i in range(32):
        if dword_value & (1 << i):
            aisles.append(i + 1)
    return aisles

def create_lighting_rules(aisles: List[int]) -> int:
    """
    Maak lighting rules DWORD van lijst aisle nummers
    
    Args:
        aisles (List[int]): Lijst van aisle nummers (1-32)
        
    Returns:
        int: 32-bit DWORD waarde
    """
    dword_value = 0
    for aisle in aisles:
        if 1 <= aisle <= 32:
            dword_value |= (1 << (aisle - 1))
    return dword_value

def validate_status_data(status: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Valideer status data en return waarschuwingen/fouten
    
    Args:
        status (Dict): Status dictionary
        
    Returns:
        Dict: Dictionary met 'warnings' en 'errors' lijsten
    """
    result = {'warnings': [], 'errors': []}
    
    # Check for alarms
    alarm_fields = [
        'alarm_light_curtain_front',
        'alarm_light_curtain_back', 
        'alarm_emergency_shutdown',
        'alarm_under_drive_section',
        'alarm_light_beam_forward',
        'alarm_light_beam_fall',
        'alarm_contactor_50k',
        'alarm_emergency_shutdown_2',
        'alarm_under_drive_section_2',
        'alarm_light_beam_forward_2',
        'alarm_light_beam_fall_2',
        'alarm_contactor_50k_2'
    ]
    
    for field in alarm_fields:
        if status.get(field, False):
            result['errors'].append(f"ALARM: {field.replace('_', ' ').title()}")
    
    # Check critical status
    if not status.get('tcp_ip_connection', False):
        result['errors'].append("TCP-IP verbinding verbroken")
    
    if not status.get('power_on', False):
        result['warnings'].append("Systeem power is uit")
    
    # Check operational modes
    auto_mode = status.get('automatic_mode_on', False)
    manual_mode = status.get('manual_mode_on', False)
    
    if not auto_mode and not manual_mode:
        result['warnings'].append("Geen operationele mode actief")
    elif auto_mode and manual_mode:
        result['warnings'].append("Beide modes tegelijk actief")
    
    if status.get('mobiles_are_moving', False):
        result['warnings'].append("Mobiles zijn in beweging")
    
    return result

def format_timestamp() -> str:
    """Return geformatteerde timestamp"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
