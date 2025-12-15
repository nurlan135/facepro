"""
FacePro GSM Modem Module
İnternet olmadıqda SMS bildiriş göndərmək üçün AT Commands wrapper.
"""

import time
from typing import Optional, Tuple
from enum import Enum

import serial
import serial.tools.list_ports

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import load_config

logger = get_logger()


class ModemStatus(Enum):
    """Modem statusları."""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


class GSMModem:
    """
    GSM Modem idarəetmə sinfi.
    USB modem vasitəsilə AT komandaları ilə SMS göndərir.
    """
    
    # AT Command timeouts
    DEFAULT_TIMEOUT = 5
    SMS_TIMEOUT = 30
    
    def __init__(
        self, 
        port: Optional[str] = None, 
        baud_rate: int = 9600,
        phone_number: str = ""
    ):
        """
        Args:
            port: COM port (məs: "COM3" və ya "/dev/ttyUSB0")
            baud_rate: Baud rate (default: 9600)
            phone_number: Default SMS nömrəsi
        """
        self._port = port
        self._baud_rate = baud_rate
        self._phone_number = phone_number
        self._serial: Optional[serial.Serial] = None
        self._status = ModemStatus.DISCONNECTED
        
        logger.info(f"GSMModem created: port={port}, baud={baud_rate}")
    
    @staticmethod
    def list_available_ports() -> list:
        """
        Mövcud COM portlarını siyahılayır.
        
        Returns:
            [(port, description, hwid), ...] siyahısı
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports
    
    @property
    def status(self) -> ModemStatus:
        """Cari modem statusu."""
        return self._status
    
    @property
    def is_connected(self) -> bool:
        """Modem qoşulubmu?"""
        return self._serial is not None and self._serial.is_open
    
    def connect(self) -> bool:
        """
        Modema qoşulur.
        
        Returns:
            Uğurlu olub-olmadığı
        """
        if self.is_connected:
            return True
        
        if not self._port:
            logger.error("No COM port specified")
            return False
        
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baud_rate,
                timeout=self.DEFAULT_TIMEOUT,
                write_timeout=self.DEFAULT_TIMEOUT
            )
            
            time.sleep(0.5)  # Modem üçün initialization vaxtı
            
            # AT test
            if self._send_command("AT"):
                self._status = ModemStatus.CONNECTED
                logger.info(f"Connected to modem: {self._port}")
                
                # SMS mode-u ayarla
                if self._send_command("AT+CMGF=1"):  # Text mode
                    self._status = ModemStatus.READY
                    logger.info("Modem ready for SMS")
                    return True
            
            self._disconnect()
            return False
            
        except serial.SerialException as e:
            logger.error(f"Serial connection failed: {e}")
            self._status = ModemStatus.ERROR
            return False
    
    def _disconnect(self):
        """Bağlantını bağlayır."""
        if self._serial:
            try:
                self._serial.close()
            except:
                pass
            self._serial = None
        self._status = ModemStatus.DISCONNECTED
    
    def disconnect(self):
        """Modemi ayırır."""
        self._disconnect()
        logger.info("Modem disconnected")
    
    def _send_command(self, command: str, timeout: int = None) -> bool:
        """
        AT komandası göndərir və cavab yoxlayır.
        
        Args:
            command: AT komandası
            timeout: Timeout saniyə
            
        Returns:
            Uğurlu olub-olmadığı (OK cavabı)
        """
        if not self.is_connected:
            return False
        
        if timeout:
            self._serial.timeout = timeout
        
        try:
            # Komandanı göndər
            self._serial.write(f"{command}\r\n".encode())
            time.sleep(0.1)
            
            # Cavabı oxu
            response = self._serial.read(256).decode('utf-8', errors='ignore')
            
            logger.debug(f"AT Command: {command} -> {response.strip()}")
            
            return "OK" in response
            
        except Exception as e:
            logger.error(f"AT command failed: {e}")
            return False
        finally:
            self._serial.timeout = self.DEFAULT_TIMEOUT
    
    def _send_sms_command(self, phone: str, message: str) -> bool:
        """
        SMS göndərmə protokolu (AT+CMGS).
        
        Args:
            phone: Telefon nömrəsi
            message: Mesaj mətni
            
        Returns:
            Uğurlu olub-olmadığı
        """
        if not self.is_connected:
            return False
        
        try:
            self._status = ModemStatus.BUSY
            
            # SMS göndərmə komandası
            self._serial.write(f'AT+CMGS="{phone}"\r\n'.encode())
            time.sleep(0.5)
            
            # Mesaj mətni
            self._serial.write(f"{message}".encode('utf-8'))
            time.sleep(0.1)
            
            # Ctrl+Z (mesajı göndər)
            self._serial.write(bytes([26]))
            
            # Cavab gözlə
            time.sleep(3)
            response = self._serial.read(256).decode('utf-8', errors='ignore')
            
            success = "OK" in response or "+CMGS" in response
            
            if success:
                logger.info(f"SMS sent to {phone}")
            else:
                logger.error(f"SMS failed: {response}")
            
            return success
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
        finally:
            self._status = ModemStatus.READY if self.is_connected else ModemStatus.DISCONNECTED
    
    def send_sms(self, message: str, phone: Optional[str] = None) -> bool:
        """
        SMS göndərir.
        
        Args:
            message: Mesaj mətni
            phone: Telefon nömrəsi (None = default)
            
        Returns:
            Uğurlu olub-olmadığı
        """
        target_phone = phone or self._phone_number
        
        if not target_phone:
            logger.error("No phone number specified")
            return False
        
        # Qoşulmamışsa, qoşul
        if not self.is_connected:
            if not self.connect():
                return False
        
        return self._send_sms_command(target_phone, message)
    
    def send_alert(self, alert_type: str = "MOTION") -> bool:
        """
        Standart xəbərdarlıq SMS-i göndərir.
        
        Args:
            alert_type: Alert növü
            
        Returns:
            Uğurlu olub-olmadığı
        """
        messages = {
            "MOTION": "DIQQQT: Obyektdə hərəkət var! (İnternet kəsilib)",
            "INTRUSION": "DIQQQT: Naməlum şxs aşkarlanib!",
            "OFFLINE": "Sistem oflayn rejimə kedi.",
            "ONLINE": "Sistem onlayn oldu."
        }
        
        message = messages.get(alert_type, f"FacePro Alert: {alert_type}")
        return self.send_sms(message)
    
    def check_signal(self) -> Tuple[bool, int]:
        """
        Siqnal gücünü yoxlayır.
        
        Returns:
            (OK, signal_strength 0-31)
        """
        if not self.is_connected:
            if not self.connect():
                return False, 0
        
        try:
            self._serial.write(b"AT+CSQ\r\n")
            time.sleep(0.5)
            response = self._serial.read(256).decode('utf-8', errors='ignore')
            
            # Parse: +CSQ: 18,0
            if "+CSQ:" in response:
                parts = response.split(":")[1].split(",")
                signal = int(parts[0].strip())
                return True, signal
            
            return False, 0
            
        except Exception as e:
            logger.error(f"Signal check failed: {e}")
            return False, 0


# Singleton instance
_modem_instance: Optional[GSMModem] = None


def get_modem() -> GSMModem:
    """Global GSMModem instance qaytarır."""
    global _modem_instance
    
    if _modem_instance is None:
        config = load_config()
        gsm_config = config.get('gsm', {})
        
        _modem_instance = GSMModem(
            port=gsm_config.get('com_port'),
            baud_rate=gsm_config.get('baud_rate', 9600),
            phone_number=gsm_config.get('phone_number', '')
        )
    
    return _modem_instance


if __name__ == "__main__":
    # Test
    print("Available COM ports:")
    for port in GSMModem.list_available_ports():
        print(f"  {port['port']}: {port['description']}")
    
    # Test connection (əgər modem varsa)
    # modem = GSMModem(port="COM3", phone_number="+994501234567")
    # if modem.connect():
    #     ok, signal = modem.check_signal()
    #     print(f"Signal: {signal}/31")
    #     modem.send_alert("MOTION")
