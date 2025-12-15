"""
FacePro - Smart Security System
================================
Lokal AI ilə işləyən ağıllı təhlükəsizlik sistemi.

Bu entry point lisenziya yoxlaması ilə başlayır.
- Lisenziya varsa -> GUI açılır
- Lisenziya yoxdursa -> GUI dialog göstərilir

(c) 2025 NurMurDev
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.utils.license_manager import check_license
from src.utils.logger import get_logger, info


def main():
    """Tətbiqin əsas entry point-i."""
    
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Application yaratmaq
    app = QApplication(sys.argv)
    app.setApplicationName("FacePro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NurMurDev")
    
    # Logger başlat
    logger = get_logger()
    info("="*50)
    info("FacePro v1.0 Starting...")
    info("="*50)
    
    # Lisenziya yoxlaması
    is_valid, message = check_license()
    
    if not is_valid:
        info(f"License check failed: {message}")
        
        # GUI License dialog göstər
        from src.ui.license_dialog import LicenseActivationDialog
        
        dialog = LicenseActivationDialog()
        result = dialog.exec()
        
        if result != dialog.DialogCode.Accepted:
            info("License activation cancelled, exiting...")
            return 1
        
        # Yenidən yoxla
        is_valid, message = check_license()
        if not is_valid:
            info("License still invalid after activation attempt")
            return 1
    
    info("License valid - starting application")
    
    # Əsas pəncərəni yaratmaq
    from src.ui.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    
    info("Application started successfully")
    
    # Event loop
    exit_code = app.exec()
    
    info("Application closed")
    info("="*50)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
