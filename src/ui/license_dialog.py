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
from PyQt6.QtGui import QColor, QCursor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.license_manager import get_machine_id, activate_license, check_license

# Modern Premium Style
MODERN_STYLE = """
QDialog {
    background-color: #0f172a;
}

QLabel {
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

QLabel#Title {
    color: #38bdf8;
    font-size: 26px;
    font-weight: bold;
    margin-bottom: 5px;
}

QLabel#Subtitle {
    color: #94a3b8;
    font-size: 14px;
}

QLabel#Label {
    color: #cbd5e1;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 2px;
}

QLineEdit {
    background-color: #1e293b;
    color: #38bdf8;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 12px;
    min-height: 25px; /* Ensure enough height for text */
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 15px;
    selection-background-color: #0ea5e9;
    margin-top: 1px; /* Fix potential clipping from layout tight spacing */
}

QLineEdit:focus {
    border: 2px solid #38bdf8;
    background-color: #1e293b;
}

QLineEdit#MachineId {
    color: #4ade80; /* Green accent */
    font-weight: bold;
    background-color: #1e293b;
    border: 1px solid #334155;
}

QPushButton {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 6px 15px; /* Reduced vertical padding */
    min-height: 24px; /* Ensure minimum height */
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px; /* Slightly smaller font to fit better */
    font-weight: 600;
}

QPushButton:hover {
    background-color: #475569;
    border-color: #64748b;
}

QPushButton#CopyBtn, QPushButton#PasteBtn {
    background-color: #334155;
    color: #f8fafc;
    border: 1px solid #475569;
}

QPushButton#CopyBtn:hover, QPushButton#PasteBtn:hover {
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
    border-color: #475569;
}

QPushButton#ActivateBtn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #2563eb);
    color: white;
    border: none;
    font-size: 15px;
    font-weight: bold;
    padding: 10px 20px; /* Larger padding for main action */
}

QPushButton#ActivateBtn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #1d4ed8);
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
        self.setWindowTitle("FacePro - Lisenziya Aktivləşdirilməsi")
        self.setFixedSize(550, 480)
        self.setStyleSheet(MODERN_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(45, 45, 45, 45)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("FacePro Lisenziyası")
        title_label.setObjectName("Title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle = QLabel("Davam etmək üçün lisenziya açarını daxil edin")
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
        form_layout.setSpacing(20)
        
        # Machine ID
        mid_layout = QVBoxLayout()
        mid_layout.setSpacing(8)
        
        lbl_mid = QLabel("Cihaz ID-niz")
        lbl_mid.setObjectName("Label")
        mid_layout.addWidget(lbl_mid)
        
        mid_row = QHBoxLayout()
        mid_row.setSpacing(10)
        
        self.machine_id = get_machine_id()
        self.machine_id_display = QLineEdit(self.machine_id)
        self.machine_id_display.setObjectName("MachineId")
        self.machine_id_display.setReadOnly(True)
        mid_row.addWidget(self.machine_id_display, 1)
        
        copy_btn = QPushButton("Kopyala")
        copy_btn.setObjectName("CopyBtn")
        copy_btn.setFixedWidth(90)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_machine_id)
        mid_row.addWidget(copy_btn)
        
        mid_layout.addLayout(mid_row)
        form_layout.addLayout(mid_layout)
        
        # License Key
        key_layout = QVBoxLayout()
        key_layout.setSpacing(8)
        
        lbl_key = QLabel("Lisenziya Açarı")
        lbl_key.setObjectName("Label")
        key_layout.addWidget(lbl_key)
        
        key_row = QHBoxLayout()
        key_row.setSpacing(10)
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX")
        # Optional: Set input mask if strict format is required, keeping it free for now but handling in logic
        # self.license_input.setInputMask("AAAA-AAAA-AAAA-AAAA-AAAA;#") 
        self.license_input.setMaxLength(29) # 20 chars + dashes if manually typed
        self.license_input.returnPressed.connect(self._activate)
        key_row.addWidget(self.license_input, 1)

        paste_btn = QPushButton("Yapışdır")
        paste_btn.setObjectName("PasteBtn")
        paste_btn.setFixedWidth(90)
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste_key)
        key_row.addWidget(paste_btn)
        
        key_layout.addLayout(key_row)
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
        
        exit_btn = QPushButton("Çıxış")
        exit_btn.setObjectName("ExitBtn")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self._exit_app)
        btn_layout.addWidget(exit_btn)
        
        activate_btn = QPushButton("Aktivləşdir")
        activate_btn.setObjectName("ActivateBtn")
        activate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        activate_btn.clicked.connect(self._activate)
        btn_layout.addWidget(activate_btn, 1) # Stretch factor 1
        
        layout.addLayout(btn_layout)
        
    def _copy_machine_id(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.machine_id)
        self._show_status("Kopyalandı!", "#4ade80")

    def _paste_key(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            # Simple cleaning or formatting if needed
            self.license_input.setText(text.strip())
            self._show_status("Yapışdırıldı!", "#38bdf8")
        
    def _show_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")
        
    def _activate(self):
        # Remove dashes for checking
        raw_key = self.license_input.text().strip().upper()
        clean_key = raw_key.replace("-", "").replace(" ", "")
        
        if not clean_key:
            self._show_status("Zəhmət olmasa lisenziya açarını daxil edin", "#facc15")
            return
            
        if len(clean_key) != 20:
            self._show_status(f"Yanlış açar uzunluğu ({len(clean_key)}/20)", "#facc15")
            return
            
        self._show_status("Lisenziya yoxlanılır...", "#38bdf8")
        QApplication.processEvents()
        
        # DEBUG: Expected key-i hesabla (Only for debug purposes, can be removed in prod)
        try:
            from src.utils.license_manager import generate_license_key
            expected_dbg = generate_license_key(self.machine_id)
        except ImportError:
            expected_dbg = "N/A"
        
        success, message = activate_license(clean_key)
        
        if success:
            self._show_status("Aktivləşdirmə Uğurlu!", "#4ade80")
            self.license_activated.emit()
            self.accept()
        else:
            # Translated error messages would ideally come from the manager, 
            # but we can wrap them or just display as is.
            # Assuming 'message' might be in English, we might want to map it 
            # or just show it alongside a generic Azerbaijani error.
            self._show_status(f"Xəta: {message}", "#f87171")
            
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
