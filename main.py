"""
FacePro - Smart Security System
================================
Lokal AI ilə işləyən ağıllı təhlükəsizlik sistemi.

Bu entry point lisenziya yoxlaması ilə başlayır.
- Lisenziya varsa -> Login sistemi yoxlanılır
- Hesab yoxdursa -> SetupWizard göstərilir
- Hesab varsa -> LoginDialog göstərilir
- Uğurlu girişdən sonra -> MainWindow açılır

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
    
    info("License valid - checking user accounts")
    
    # User authentication system
    from src.utils.auth_manager import get_auth_manager
    from src.ui.setup_wizard import SetupWizardDialog
    from src.ui.login_dialog import LoginDialog
    
    auth_manager = get_auth_manager()
    
    # Check if any user accounts exist
    if not auth_manager.has_accounts():
        info("No user accounts found - showing setup wizard")
        
        # First-time setup: create admin account
        setup_dialog = SetupWizardDialog()
        result = setup_dialog.exec()
        
        if result != setup_dialog.DialogCode.Accepted:
            info("Setup wizard cancelled, exiting...")
            return 1
        
        info("Admin account created successfully")
    
    # Show login dialog
    info("Showing login dialog")
    login_dialog = LoginDialog()
    result = login_dialog.exec()
    
    if result != login_dialog.DialogCode.Accepted:
        info("Login cancelled, exiting...")
        return 1
    
    # Get current user info for logging
    current_user = auth_manager.get_current_user()
    if current_user:
        info(f"User '{current_user.username}' logged in as {current_user.role}")
    
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
