"""
TCP-IP Client voor Mobile Racking communicatie
Gebaseerd op WMS protocol specificatie
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
    """TCP-IP client voor communicatie met Mobile Racking systeem"""
    
    def __init__(self, host: str = "1.1.1.2", port: int = 2000):
        """
        Initialiseer TCP client
        
        Args:
            host (str): IP adres van de Mobile Racking controller
            port (int): TCP poort (standaard 2000)
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Maak verbinding met de Mobile Racking controller
        
        Returns:
            bool: True als verbinding succesvol, False anders
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)  # 10 seconden timeout voor PLC via VPN
            
            logger.info(f"Proberen verbinding naar {self.host}:{self.port}...")
            start_time = time.time()
            
            self.socket.connect((self.host, self.port))
            
            end_time = time.time()
            connect_time = (end_time - start_time) * 1000
            
            self.connected = True
            logger.info(f"Verbonden met {self.host}:{self.port} in {connect_time:.0f}ms")
            return True
            
        except socket.timeout:
            logger.error(f"Verbinding timeout naar {self.host}:{self.port} (>10s)")
            self.connected = False
            return False
        except ConnectionRefusedError:
            logger.error(f"Verbinding geweigerd door {self.host}:{self.port} - Service niet actief")
            self.connected = False
            return False
        except socket.gaierror as e:
            logger.error(f"DNS/Host resolutie fout: {e}")
            self.connected = False
            return False
        except OSError as e:
            if e.errno == 10061:
                logger.error(f"Verbinding geweigerd (Error 10061) - Poort {self.port} niet open op {self.host}")
            elif e.errno == 10060:
                logger.error(f"Verbinding timeout (Error 10060) - Host niet bereikbaar")
            else:
                logger.error(f"OS Error {e.errno}: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Onbekende fout bij verbinden: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Verbreek verbinding"""
        if self.socket:
            try:
                self.socket.close()
                logger.info("Verbinding verbroken")
            except:
                pass
            finally:
                self.socket = None
                self.connected = False
    
    def send_command(self, command: int) -> Optional[bytes]:
        """
        Verzend een 2-byte command en ontvang 20-byte response
        
        Args:
            command (int): Command nummer (0-65535)
            
        Returns:
            Optional[bytes]: 20-byte response of None bij fout
        """
        if not self.connected or not self.socket:
            logger.error("Geen verbinding")
            return None
            
        try:
            # Verstuur 2-byte command (little endian)
            command_bytes = struct.pack('<H', command)
            
            logger.debug(f"Verzenden command: {command} ({command_bytes.hex()})")
            self.socket.send(command_bytes)
            
            # Ontvang 20-byte response met timeout handling
            response = b""
            start_time = time.time()
            max_wait_time = 5.0  # 5 seconden timeout voor response
            
            while len(response) < 20:
                # Check timeout
                if time.time() - start_time > max_wait_time:
                    logger.error(f"Timeout bij ontvangen response na {max_wait_time}s")
                    self.connected = False
                    return None
                
                try:
                    # Ontvang met korte timeout per chunk
                    self.socket.settimeout(1.0)
                    chunk = self.socket.recv(20 - len(response))
                    
                    if not chunk:
                        logger.error("Verbinding verbroken tijdens ontvangst")
                        self.connected = False
                        return None
                        
                    response += chunk
                    logger.debug(f"Chunk ontvangen: {len(chunk)} bytes, totaal: {len(response)}/20")
                    
                except socket.timeout:
                    # Korte timeout is OK, probeer opnieuw
                    continue
                except socket.error as e:
                    logger.error(f"Socket error tijdens ontvangst: {e}")
                    self.connected = False
                    return None
            
            # Reset socket timeout naar origineel
            self.socket.settimeout(10.0)
            
            logger.debug(f"Volledige response ontvangen: {response.hex()}")
            return response
            
        except socket.error as e:
            logger.error(f"Communicatie fout: {e}")
            self.connected = False
            return None
        except Exception as e:
            logger.error(f"Onbekende fout bij send_command: {e}")
            self.connected = False
            return None
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """
        Haal volledige status op van het Mobile Racking systeem
        
        Returns:
            Optional[Dict]: Status dictionary of None bij fout
        """
        response = self.send_command(0)  # Status request command
        if response:
            return self.parse_status_response(response)
        return None
    
    def parse_status_response(self, response: bytes) -> Dict[str, Any]:
        """
        Parse de 20-byte status response volgens WMS specificatie
        
        Args:
            response (bytes): 20-byte response
            
        Returns:
            Dict: Geparsde status data
        """
        if len(response) != 20:
            logger.error(f"Ongeldige response lengte: {len(response)} (verwacht 20)")
            return {}
        
        try:
            # Parse volgens WMS-Data structuur
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
            logger.error(f"Fout bij parsen response: {e}")
            return {}
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
