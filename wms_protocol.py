"""
WMS Protocol Definition
Based on Mobile Racking WMS-Data specification
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class DataType(Enum):
    """Data types according to WMS specification"""
    BOOL = "Bool"
    BYTE = "Byte" 
    DWORD = "DWord"

@dataclass
class WMSField:
    """WMS data field definition"""
    name: str
    data_type: DataType
    offset: float
    start_value: Any
    comment: str
    
# WMS-Data structure according to specification
WMS_DATA_STRUCTURE = {
    'command_request': WMSField(
        name="Command: Request A...",
        data_type=DataType.BYTE,
        offset=0.0,
        start_value=1640,
        comment="Integer: 1..19"
    ),
    'command_start_operation': WMSField(
        name="Command: Start Ope...",
        data_type=DataType.BOOL,
        offset=1.0,
        start_value=False,
        comment="True = Send"
    ),
    'command_request_status': WMSField(
        name="Command: Request St...",
        data_type=DataType.BOOL,
        offset=1.1,
        start_value=False,
        comment="Always false = Send / Option by TCP-IP Connection"
    ),
    'stow_mobile_racking_major': WMSField(
        name="Stow Mobile Racking ...",
        data_type=DataType.BYTE,
        offset=2.0,
        start_value=2,
        comment='Mobile Racking Software Version "Major"'
    ),
    'stow_mobile_racking_minor': WMSField(
        name="Stow Mobile Racking ...",
        data_type=DataType.BYTE,
        offset=3.0,
        start_value=5,
        comment='Mobile Racking Software Version "Minor"'
    ),
    'tcp_ip_reserved_message': WMSField(
        name="TCP IP Reserved Messa...",
        data_type=DataType.BYTE,
        offset=4.0,
        start_value=1640,
        comment="Integer"
    ),
    'tcp_ip_connection': WMSField(
        name="TCP IP Connection",
        data_type=DataType.BOOL,
        offset=5.0,
        start_value=False,
        comment="True = OK"
    ),
    'automatic_mode_on': WMSField(
        name="Automatic Mode is ON",
        data_type=DataType.BOOL,
        offset=5.1,
        start_value=False,
        comment="True = OK"
    ),
    'mobiles_are_released': WMSField(
        name="Mobiles Are Released I...",
        data_type=DataType.BOOL,
        offset=5.2,
        start_value=False,
        comment="True = OK"
    ),
    'manual_mode_on': WMSField(
        name="Manual Mode is ON",
        data_type=DataType.BOOL,
        offset=5.3,
        start_value=False,
        comment="True = OK"
    ),
    'night_mode_activated': WMSField(
        name="Night Mode Activated",
        data_type=DataType.BOOL,
        offset=5.4,
        start_value=False,
        comment="True = OK"
    ),
    'mobiles_are_moving': WMSField(
        name="Mobiles Are Moving",
        data_type=DataType.BOOL,
        offset=5.5,
        start_value=False,
        comment="True = OK"
    ),
    'power_on': WMSField(
        name="Power ON",
        data_type=DataType.BOOL,
        offset=5.6,
        start_value=False,
        comment="True = OK"
    ),
    'mobile_quantity': WMSField(
        name="Mobile Quantity",
        data_type=DataType.BYTE,
        offset=6.0,
        start_value=1640,
        comment="Integer"
    ),
    'counter_lift_track_inside': WMSField(
        name="Counter: Lifttrack inside",
        data_type=DataType.BYTE,
        offset=7.0,
        start_value=1640,
        comment="Integer"
    ),
    'alarm_light_curtain_front': WMSField(
        name="Alarm: Light Curtain Fr...",
        data_type=DataType.BOOL,
        offset=8.0,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_light_curtain_back': WMSField(
        name="Alarm: Light Curtain Ba...",
        data_type=DataType.BOOL,
        offset=8.1,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_emergency_shutdown': WMSField(
        name="Alarm: Emergency Shu...",
        data_type=DataType.BOOL,
        offset=8.2,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_under_drive_section': WMSField(
        name="Alarm: Under Drive Se...",
        data_type=DataType.BOOL,
        offset=8.3,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_light_beam_forward': WMSField(
        name="Alarm: Light Beam For...",
        data_type=DataType.BOOL,
        offset=8.4,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_light_beam_fall': WMSField(
        name="Alarm: Light Beam Fall...",
        data_type=DataType.BOOL,
        offset=8.5,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_contactor_50k': WMSField(
        name="Alarm: Contactor 50k...",
        data_type=DataType.BOOL,
        offset=8.6,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_emergency_shutdown_2': WMSField(
        name="Alarm: Emergency Shu...",
        data_type=DataType.BOOL,
        offset=9.0,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_under_drive_section_2': WMSField(
        name="Alarm: Under Drive Se...",
        data_type=DataType.BOOL,
        offset=9.1,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_light_beam_forward_2': WMSField(
        name="Alarm: Light Beam For...",
        data_type=DataType.BOOL,
        offset=9.2,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_light_beam_fall_2': WMSField(
        name="Alarm: Light Beam Fall...",
        data_type=DataType.BOOL,
        offset=9.3,
        start_value=False,
        comment="True = Alarm"
    ),
    'alarm_contactor_50k_2': WMSField(
        name="Alarm: Contactor 50k...",
        data_type=DataType.BOOL,
        offset=9.4,
        start_value=False,
        comment="True = Alarm"
    ),
    'lighting_rules': WMSField(
        name="Lighting Rules",
        data_type=DataType.DWORD,
        offset=10.0,
        start_value=1640,
        comment="lowest bit = aisle 1, highest bit = aisle 32, bit set = light on, little endian"
    ),
    'selected_aisle_to_open': WMSField(
        name="Selected Aisle to Open",
        data_type=DataType.BYTE,
        offset=14.0,
        start_value=1640,
        comment="Integer"
    )
}

class WMSCommands:
    """
    WMS Command definitions according to PDF specification
    
    According to PDF:
    - Status request: first byte = 0, second byte = 2  
    - Open aisle: first byte = aisle number (1-19), second byte = 1
    """
    
    # Status command (converted to bytes 0,2)
    STATUS_REQUEST = 0
    
    # Aisle commands (converted to aisle_number,1)
    OPEN_AISLE_1 = 1
    OPEN_AISLE_2 = 2
    OPEN_AISLE_3 = 3
    OPEN_AISLE_4 = 4
    OPEN_AISLE_5 = 5
    OPEN_AISLE_6 = 6
    OPEN_AISLE_7 = 7
    OPEN_AISLE_8 = 8
    OPEN_AISLE_9 = 9
    OPEN_AISLE_10 = 10
    OPEN_AISLE_11 = 11
    OPEN_AISLE_12 = 12
    OPEN_AISLE_13 = 13
    OPEN_AISLE_14 = 14
    OPEN_AISLE_15 = 15
    OPEN_AISLE_16 = 16
    OPEN_AISLE_17 = 17
    OPEN_AISLE_18 = 18
    OPEN_AISLE_19 = 19
    
    # Legacy commands for compatibility (will use old format)
    START_OPERATION = 100
    STOP_OPERATION = 101
    SET_AUTOMATIC_MODE = 102
    SET_MANUAL_MODE = 103
    SET_NIGHT_MODE = 104
    RELEASE_MOBILES = 105
    LOCK_MOBILES = 106
    OPEN_AISLE = 30
    CLOSE_AISLE = 31

def get_status_description(status: Dict[str, Any]) -> Dict[str, str]:
    """
    Convert status values to readable descriptions
    
    Args:
        status (Dict): Status dictionary from TCP client
        
    Returns:
        Dict: Dictionary with readable descriptions
    """
    descriptions = {}
    
    for key, value in status.items():
        if key in WMS_DATA_STRUCTURE:
            field = WMS_DATA_STRUCTURE[key]
            if field.data_type == DataType.BOOL:
                descriptions[key] = "OK" if value else "NOT OK"
            else:
                descriptions[key] = str(value)
        else:
            descriptions[key] = str(value)
    
    return descriptions
