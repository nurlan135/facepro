"""
FacePro Login Dialog Module
User authentication dialog with dark theme.

Requirements: 2.1, 2.5
"""

import os
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QApplication,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.auth_manager import get_auth_manager
from src.utils.i18n import tr
from src.ui.styles import COLORS


LOGIN_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg_dark']};
}}
QLabel {{
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', sans-serif;
    background-color: transparent;
}}
QLabel#Title {{
    color: {COLORS['primary']};
    font-size: 28px;
    font-weight: bold;
}}
QLabel#Subtitle {{
    color: {COLORS['text_secondary']};
    font-size: 14px;
}}
QLabel#FieldLabel {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
    font-weight: 600;
}}
QLabel#ErrorLabel {{
    color: {COLORS['danger']};
    font-size: 13px;
    font-weight: 500;
    padding: 8px;
    background-color: rgba(231, 76, 60, 0.1);
    border-radius: 6px;
}}
QLabel#LockedLabel {{
    color: {COLORS['warning']};
    font-size: 13px;
    font-weight: 600;
    padding: 10px;
    background-color: rgba(241, 196, 15, 0.15);
    border: 1px solid {COLORS['warning']};
    border-radius: 6px;
}}
QLineEdit {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 12px 16px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    selection-background-color: {COLORS['primary']};
}}
QLineEdit:focus {{
    border: 2px solid {COLORS['primary']};
    background-color: {COLORS['bg_light']};
}}
QLineEdit:disabled {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
}}
QPushButton {{
    border-radius: 8px;
    padding: 12px 24px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#LoginBtn {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    font-size: 15px;
    min-height: 20px;
}}
QPushButton#LoginBtn:hover {{
    background-color: {COLORS['primary_hover']};
}}
QPushButton#LoginBtn:pressed {{
    background-color: #1d4ed8;
}}
QPushButton#LoginBtn:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}
QPushButton#ExitBtn {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
}}
QPushButton#ExitBtn:hover {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border-color: {COLORS['border_light']};
}}
QFrame#Divider {{
    background-color: {COLORS['border']};
    max-height: 1px;
}}
"""


class LoginDialog(QDialog):
    """Login dialog for user authentication."""
    
    login_successful = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth_manager = get_auth_manager()
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle(tr("login_title"))
        self.setFixedSize(440, 480)
        self.setStyleSheet(LOGIN_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 40, 50, 40)
        
        self._create_header(layout)
        
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)
        
        self._create_form(layout)
        self._create_status_area(layout)
        
        layout.addSpacerItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))
        
        self._create_buttons(layout)
        self.username_input.setFocus()
    
    def _create_header(self, layout: QVBoxLayout):
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("FacePro")
        title_label.setObjectName("Title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle = QLabel(tr("login_subtitle"))
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
    
    def _create_form(self, layout: QVBoxLayout):
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(6)
        
        username_label = QLabel(tr("login_username"))
        username_label.setObjectName("FieldLabel")
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(tr("login_username_placeholder"))
        self.username_input.returnPressed.connect(self._focus_password)
        username_layout.addWidget(self.username_input)
        
        form_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(6)
        
        password_label = QLabel(tr("login_password"))
        password_label.setObjectName("FieldLabel")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(tr("login_password_placeholder"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._attempt_login)
        password_layout.addWidget(self.password_input)
        
        form_layout.addLayout(password_layout)
        
        layout.addLayout(form_layout)
    
    def _create_status_area(self, layout: QVBoxLayout):
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        self.locked_label = QLabel("🔒 " + tr("login_account_locked"))
        self.locked_label.setObjectName("LockedLabel")
        self.locked_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.locked_label.setWordWrap(True)
        self.locked_label.setVisible(False)
        layout.addWidget(self.locked_label)
    
    def _create_buttons(self, layout: QVBoxLayout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        exit_btn = QPushButton(tr("login_btn_exit"))
        exit_btn.setObjectName("ExitBtn")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self._exit_app)
        btn_layout.addWidget(exit_btn)
        
        self.login_btn = QPushButton(tr("login_btn_signin"))
        self.login_btn.setObjectName("LoginBtn")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._attempt_login)
        btn_layout.addWidget(self.login_btn, 1)
        
        layout.addLayout(btn_layout)
    
    def _focus_password(self):
        self.password_input.setFocus()
    
    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.locked_label.setVisible(False)
    
    def _show_locked(self, message: str):
        self.locked_label.setText(f"🔒 {message}")
        self.locked_label.setVisible(True)
        self.error_label.setVisible(False)
    
    def _clear_status(self):
        self.error_label.setVisible(False)
        self.locked_label.setVisible(False)
    
    def _attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            self._show_error(tr("login_error_username"))
            self.username_input.setFocus()
            return
        
        if not password:
            self._show_error(tr("login_error_password"))
            self.password_input.setFocus()
            return
        
        self._clear_status()
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText(tr("login_signing_in"))
        QApplication.processEvents()
        
        success, message = self._auth_manager.authenticate(username, password)
        
        self.login_btn.setEnabled(True)
        self.login_btn.setText(tr("login_btn_signin"))
        
        if success:
            self.login_successful.emit()
            self.accept()
        else:
            if "locked" in message.lower():
                self._show_locked(message)
            else:
                self._show_error(message)
            
            self.password_input.clear()
            self.password_input.setFocus()
    
    def _exit_app(self):
        self.reject()
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self._exit_app()
        else:
            super().keyPressEvent(event)


def show_login_dialog() -> bool:
    dialog = LoginDialog()
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    result = dialog.exec()
    print(f"Dialog result: {result}")
