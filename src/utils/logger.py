"""
FacePro Logger Module
Tətbiq üçün mərkəzləşdirilmiş logging sistemi.
Fayl və konsol çıxışını dəstəkləyir.
"""

import logging
import os
from datetime import datetime
from typing import Optional


class FaceProLogger:
    """FacePro üçün xüsusi logger sinfi."""
    
    _instance: Optional['FaceProLogger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern - yalnız bir instance yaradılır."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Logger-i konfiqurasiya edir."""
        if FaceProLogger._initialized:
            return
            
        self.logger = logging.getLogger('FacePro')
        self.logger.setLevel(logging.DEBUG)
        
        # Formatter - loqların formatı
        self.formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
        
        # File Handler - logs qovluğuna yazır
        self._setup_file_handler()
        
        FaceProLogger._initialized = True
        self.logger.info("FacePro Logger initialized")
    
    def _setup_file_handler(self):
        """Fayl handler-i qurur."""
        # Logs qovluğunu yarat
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'logs'
        )
        os.makedirs(log_dir, exist_ok=True)
        
        # Gündəlik log faylı
        log_file = os.path.join(
            log_dir, 
            f"facepro_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """Debug səviyyəsində log."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Info səviyyəsində log."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Warning səviyyəsində log."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Error səviyyəsində log."""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Critical səviyyəsində log."""
        self.logger.critical(message)
    
    def exception(self, message: str):
        """Exception ilə birlikdə log (traceback daxil)."""
        self.logger.exception(message)


# Global logger instance
_logger: Optional[FaceProLogger] = None


def get_logger() -> FaceProLogger:
    """Global logger instance-ı qaytarır."""
    global _logger
    if _logger is None:
        _logger = FaceProLogger()
    return _logger


# Sadə interfeys funksiyaları
def debug(message: str):
    get_logger().debug(message)

def info(message: str):
    get_logger().info(message)

def warning(message: str):
    get_logger().warning(message)

def error(message: str):
    get_logger().error(message)

def critical(message: str):
    get_logger().critical(message)

def exception(message: str):
    get_logger().exception(message)


if __name__ == "__main__":
    # Test
    info("Bu info mesajidir")
    warning("Bu warning mesajidir")
    error("Bu error mesajidir")
    debug("Bu debug mesajidir")
