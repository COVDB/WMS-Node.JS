"""
TCP-IP Client for Mobile Racking communication
Based on WMS protocol specification
"""

import socket
import struct
import time
from typing import Optional, Tuple, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TCPClient:
    """TCP-IP client for communication with Mobile Racking system"""
    
    def __init__(self, host: str = "1.1.1.2", port: int = 2000):
        """
        Initialize TCP client
        
        Args:
            host (str): IP address of the Mobile Racking controller
            port (int): TCP port (default 2000 per PDF documentation)
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Connect to the Mobile Racking controller
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # 10 second timeout for PLC via VPN
            
            logger.info(f"Attempting connection to {self.host}:{self.port}...")
            start_time = time.time()
            
            self.socket.connect((self.host, self.port))
            
            end_time = time.time()
            connect_time = (end_time - start_time) * 1000
            
            self.connected = True
            logger.info(f"Connected to {self.host}:{self.port} in {connect_time:.0f}ms")
            return True
            
        except socket.timeout:
            logger.error(f"Connection timeout to {self.host}:{self.port} (>10s)")
            self.connected = False
            return False
        except ConnectionRefusedError:
            logger.error(f"Connection refused by {self.host}:{self.port} - Service not active")
            self.connected = False
            return False
        except socket.gaierror as e:
            logger.error(f"DNS/Host resolution error: {e}")
            self.connected = False
            return False
        except OSError as e:
            if e.errno == 10061:
                logger.error(f"Connection refused (Error 10061) - Port {self.port} not open on {self.host}")
            elif e.errno == 10060:
                logger.error(f"Connection timeout (Error 10060) - Host not reachable")
            else:
                logger.error(f"OS Error {e.errno}: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unknown error during connection: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the controller"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Connection closed")
            except:
                pass
            finally:
                self.socket = None
                self.connected = False
    
    def send_command(self, command: int) -> Optional[bytes]:
        """
        Send a 2-byte command and receive 20-byte response
        According to PDF: Status request = (0,2), Open aisle = (aisle_num,1)
        
        Args:
            command (int): Command number (0=status, 1-19=open aisle)
            
        Returns:
            Optional[bytes]: 20-byte response or None on error
        """
        if not self.connected or not self.socket:
            logger.error("No connection")
            return None
            
        try:
            # Prepare command according to PDF specification
            if command == 0:
                # Status request: first byte = 0, second byte = 2
                command_bytes = struct.pack('BB', 0, 2)
                logger.debug(f"Sending status request: (0, 2) = {command_bytes.hex()}")
            elif 1 <= command <= 19:
                # Open aisle: first byte = aisle number, second byte = 1
                command_bytes = struct.pack('BB', command, 1)
                logger.debug(f"Sending open aisle {command}: ({command}, 1) = {command_bytes.hex()}")
            else:
                # Custom command (fallback to old format)
                command_bytes = struct.pack('<H', command)
                logger.debug(f"Sending custom command: {command} = {command_bytes.hex()}")
            
            self.socket.send(command_bytes)
            
            # Receive 20-byte response with timeout handling
            response = b""
            start_time = time.time()
            max_wait_time = 5.0  # 5 second timeout for response
            
            while len(response) < 20:
                # Check timeout
                if time.time() - start_time > max_wait_time:
                    logger.error(f"Timeout receiving response after {max_wait_time}s")
                    self.connected = False
                    return None
                
                try:
                    # Receive with short timeout per chunk
                    self.socket.settimeout(1.0)
                    chunk = self.socket.recv(20 - len(response))
                    
                    if not chunk:
                        logger.error("Connection broken during receive")
                        self.connected = False
                        return None
                        
                    response += chunk
                    logger.debug(f"Chunk received: {len(chunk)} bytes, total: {len(response)}/20")
                    
                except socket.timeout:
                    # Short timeout is OK, try again
                    continue
                except socket.error as e:
                    logger.error(f"Socket error during receive: {e}")
                    self.connected = False
                    return None
            
            # Reset socket timeout to original
            self.socket.settimeout(10.0)
            
            logger.debug(f"Complete response received: {response.hex()}")
            return response
            
        except socket.error as e:
            logger.error(f"Communication error: {e}")
            self.connected = False
            return None
        except Exception as e:
            logger.error(f"Unknown error in send_command: {e}")
            self.connected = False
            return None
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Get complete status from the Mobile Racking system
        
        Returns:
            Optional[Dict]: Status dictionary or None on error
        """
        response = self.send_command(0)  # Status request command
        if response:
            return self.parse_status_response(response)
        return None
    
    def parse_status_response(self, response: bytes) -> Dict[str, Any]:
        """
        Parse the 20-byte status response according to WMS specification
        
        Args:
            response (bytes): 20-byte response
            
        Returns:
            Dict: Parsed status data
        """
        if len(response) != 20:
            logger.error(f"Invalid response length: {len(response)} (expected 20)")
            return {}
        
        try:
            # Parse according to WMS-Data structure
            status = {}
            
            # Byte 0-1: Command Request (Byte)
            status['command_request'] = struct.unpack('<H', response[0:2])[0]
            
            # Byte 2: Command Start Operation (Bool)
            status['command_start_operation'] = bool(response[2])
            
            # Byte 3: Command Request Status (Bool)  
            status['command_request_status'] = bool(response[3])
            
            # Byte 4: Stow Mobile Racking Major (Byte)
            status['stow_mobile_racking_major'] = response[4]
            
            # Byte 5: Stow Mobile Racking Minor (Byte)
            status['stow_mobile_racking_minor'] = response[5]
            
            # Byte 6-7: TCP IP Reserved Message (Byte)
            status['tcp_ip_reserved_message'] = struct.unpack('<H', response[6:8])[0]
            
            # Byte 8: TCP IP Connection (Bool)
            status['tcp_ip_connection'] = bool(response[8])
            
            # Byte 9: Automatic Mode is ON (Bool)
            status['automatic_mode_on'] = bool(response[9])
            
            # Byte 10: Mobiles Are Released (Bool)
            status['mobiles_are_released'] = bool(response[10])
            
            # Byte 11: Manual Mode is ON (Bool)
            status['manual_mode_on'] = bool(response[11])
            
            # Byte 12: Night Mode Activated (Bool)
            status['night_mode_activated'] = bool(response[12])
            
            # Byte 13: Mobiles Are Moving (Bool)
            status['mobiles_are_moving'] = bool(response[13])
            
            # Byte 14: Power ON (Bool)
            status['power_on'] = bool(response[14])
            
            # Byte 15: Mobile Quantity (Byte)
            status['mobile_quantity'] = response[15]
            
            # Byte 16-17: Counter Lift-track inside (Byte)
            status['counter_lift_track_inside'] = struct.unpack('<H', response[16:18])[0]
            
            # Byte 18: Alarm Light Curtain Front (Bool)
            status['alarm_light_curtain_front'] = bool(response[18])
            
            # Byte 19: Alarm Light Curtain Back (Bool)
            status['alarm_light_curtain_back'] = bool(response[19])
            
            return status
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {}
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
