"""
FacePro License Activation Dialog Module
GUI-based license activation.
"""

import os
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QApplication, 
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.license_manager import get_machine_id, activate_license, check_license

# Modern Style
MODERN_STYLE = """
QDialog {
    background-color: #1e293b; 
}

QLabel {
    color: #e2e8f0;
    font-family: 'Segoe UI', sans-serif;
}

QLabel#Title {
    color: #38bdf8;
    font-size: 24px;
    font-weight: bold;
}

QLabel#Subtitle {
    color: #94a3b8;
    font-size: 14px;
}

QLabel#Label {
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 600;
}

QLineEdit {
    background-color: #0f172a;
    color: #38bdf8;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 12px;
    font-family: 'Consolas', monospace;
    font-size: 15px;
    selection-background-color: #0ea5e9;
}

QLineEdit:focus {
    border: 2px solid #38bdf8;
    background-color: #0f172a;
}

QLineEdit#MachineId {
    color: #4ade80;
    font-weight: bold;
    background-color: #0f172a;
    border: 1px solid #334155;
}

QPushButton {
    border-radius: 8px;
    padding: 12px 20px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 600;
}

QPushButton#CopyBtn {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
}

QPushButton#CopyBtn:hover {
    background-color: #475569;
    border-color: #64748b;
}

QPushButton#ExitBtn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid #334155;
}

QPushButton#ExitBtn:hover {
    background-color: #334155;
    color: #f8fafc;
}

QPushButton#ActivateBtn {
    background-color: #0ea5e9;
    color: white;
    border: none;
    font-size: 15px;
}

QPushButton#ActivateBtn:hover {
    background-color: #0284c7;
}

QPushButton#ActivateBtn:pressed {
    background-color: #0369a1;
}
"""

class LicenseActivationDialog(QDialog):
    """
    Lisenziya aktivasiyası üçün GUI dialog.
    """
    
    license_activated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle("FacePro - License Activation")
        self.setFixedSize(520, 440)
        self.setStyleSheet(MODERN_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        title_label = QLabel("FacePro License")
        title_label.setObjectName("Title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle = QLabel("Please enter your license key to continue")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #334155; max-height: 1px;")
        layout.addWidget(line)
        
        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Machine ID
        mid_layout = QVBoxLayout()
        mid_layout.setSpacing(8)
        
        lbl_mid = QLabel("Your Machine ID")
        lbl_mid.setObjectName("Label")
        mid_layout.addWidget(lbl_mid)
        
        mid_row = QHBoxLayout()
        mid_row.setSpacing(10)
        
        self.machine_id = get_machine_id()
        self.machine_id_display = QLineEdit(self.machine_id)
        self.machine_id_display.setObjectName("MachineId")
        self.machine_id_display.setReadOnly(True)
        mid_row.addWidget(self.machine_id_display, 1)
        
        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("CopyBtn")
        copy_btn.setFixedWidth(80)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_machine_id)
        mid_row.addWidget(copy_btn)
        
        mid_layout.addLayout(mid_row)
        form_layout.addLayout(mid_layout)
        
        # License Key
        key_layout = QVBoxLayout()
        key_layout.setSpacing(8)
        
        lbl_key = QLabel("License Key")
        lbl_key.setObjectName("Label")
        key_layout.addWidget(lbl_key)
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX")
        self.license_input.setMaxLength(25) # 20 chars + potential dashes
        self.license_input.returnPressed.connect(self._activate)
        key_layout.addWidget(self.license_input)
        
        form_layout.addLayout(key_layout)
        
        layout.addLayout(form_layout)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        self.status_label.setWordWrap(True)  # Enable multi-line text
        self.status_label.setMinimumHeight(40) # Give it space
        layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        exit_btn = QPushButton("Exit Protocol")
        exit_btn.setObjectName("ExitBtn")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self._exit_app)
        btn_layout.addWidget(exit_btn)
        
        activate_btn = QPushButton("Activate License")
        activate_btn.setObjectName("ActivateBtn")
        activate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        activate_btn.clicked.connect(self._activate)
        btn_layout.addWidget(activate_btn, 1) # Stretch factor 1
        
        layout.addLayout(btn_layout)
        
    def _copy_machine_id(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.machine_id)
        self._show_status("Copied to clipboard!", "#4ade80")
        
    def _show_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")
        
    def _activate(self):
        # Remove dashes for checking
        raw_key = self.license_input.text().strip().upper()
        clean_key = raw_key.replace("-", "").replace(" ", "")
        
        if not clean_key:
            self._show_status("Please enter a license key", "#facc15")
            return
            
        if len(clean_key) != 20:
            self._show_status(f"Invalid key length ({len(clean_key)}/20)", "#facc15")
            return
            
        self._show_status("Verifying license...", "#38bdf8")
        QApplication.processEvents()
        
        machine_id = get_machine_id()
        # DEBUG: Expected key-i hesabla
        from src.utils.license_manager import generate_license_key
        expected_dbg = generate_license_key(machine_id)
        
        success, message = activate_license(clean_key)
        
        if success:
            self._show_status("Activation Successful!", "#4ade80")
            self.license_activated.emit()
            self.accept()
        else:
            self._show_status(f"Error: {message} (Exp: {expected_dbg})", "#f87171")
            
    def _exit_app(self):
        self.reject()

def show_license_dialog_if_needed() -> bool:
    is_valid, _ = check_license()
    if is_valid:
        return True
    
    dialog = LicenseActivationDialog()
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LicenseActivationDialog()
    dialog.exec()
