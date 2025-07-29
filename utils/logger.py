"""
Logging utilities voor WMS systeem
"""

import logging
import os
from datetime import datetime
from typing import Optional

class WMSLogger:
    """Custom logger voor WMS applicatie"""
    
    def __init__(self, name: str = "WMS", log_file: Optional[str] = None):
        """
        Initialiseer logger
        
        Args:
            name (str): Logger naam
            log_file (Optional[str]): Pad naar log bestand
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Voorkomen van duplicate handlers
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # File handler (optioneel)
            if log_file:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def log_connection(self, host: str, port: int, success: bool):
        """Log verbinding poging"""
        status = "succesvol" if success else "mislukt"
        self.info(f"Verbinding naar {host}:{port} {status}")
    
    def log_command(self, command: int, response_length: Optional[int] = None):
        """Log command verzending"""
        if response_length is not None:
            self.info(f"Command {command} verzonden, {response_length} bytes ontvangen")
        else:
            self.warning(f"Command {command} verzonden, geen response")
    
    def log_status_update(self, status_summary: str):
        """Log status update"""
        self.info(f"Status update: {status_summary}")
    
    def log_alarm(self, alarm_type: str):
        """Log alarm"""
        self.error(f"ALARM: {alarm_type}")

# Global logger instance
wms_logger = WMSLogger("WMS-App", "logs/wms.log")
