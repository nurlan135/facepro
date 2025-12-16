"""
FacePro Login Dialog Module
User authentication dialog with dark theme.

Requirements: 2.1, 2.5
- Display login dialog before showing main dashboard
- Show application logo and dark-themed interface
- Username/Password fields with Enter key support
- Error message display area
- Account locked indicator
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
from src.ui.styles import COLORS


# Login Dialog Style - Dark theme consistent with app
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

QLabel#SuccessLabel {{
    color: {COLORS['success']};
    font-size: 13px;
    font-weight: 500;
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
    """
    Login dialog for user authentication.
    
    Features:
    - Dark theme consistent with main application
    - Username/Password fields
    - Login button with Enter key support
    - Error message display area
    - Account locked indicator
    
    Signals:
        login_successful: Emitted when login succeeds
    """
    
    login_successful = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth_manager = get_auth_manager()
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("FacePro - Login")
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
        
        # Header section
        self._create_header(layout)
        
        # Divider
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)
        
        # Form section
        self._create_form(layout)
        
        # Status/Error section
        self._create_status_area(layout)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))
        
        # Buttons section
        self._create_buttons(layout)
        
        # Set focus to username field
        self.username_input.setFocus()
    
    def _create_header(self, layout: QVBoxLayout):
        """Create header with title and subtitle."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Title
        title_label = QLabel("FacePro")
        title_label.setObjectName("Title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("Sign in to continue")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
    
    def _create_form(self, layout: QVBoxLayout):
        """Create login form with username and password fields."""
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(6)
        
        username_label = QLabel("Username")
        username_label.setObjectName("FieldLabel")
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.returnPressed.connect(self._focus_password)
        username_layout.addWidget(self.username_input)
        
        form_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(6)
        
        password_label = QLabel("Password")
        password_label.setObjectName("FieldLabel")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._attempt_login)
        password_layout.addWidget(self.password_input)
        
        form_layout.addLayout(password_layout)
        
        layout.addLayout(form_layout)
    
    def _create_status_area(self, layout: QVBoxLayout):
        """Create status/error message display area."""
        # Error label (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Locked indicator (hidden by default)
        self.locked_label = QLabel("🔒 Account is locked")
        self.locked_label.setObjectName("LockedLabel")
        self.locked_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.locked_label.setWordWrap(True)
        self.locked_label.setVisible(False)
        layout.addWidget(self.locked_label)
    
    def _create_buttons(self, layout: QVBoxLayout):
        """Create login and exit buttons."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # Exit button
        exit_btn = QPushButton("Exit")
        exit_btn.setObjectName("ExitBtn")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self._exit_app)
        btn_layout.addWidget(exit_btn)
        
        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("LoginBtn")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._attempt_login)
        btn_layout.addWidget(self.login_btn, 1)  # Stretch factor
        
        layout.addLayout(btn_layout)
    
    def _focus_password(self):
        """Move focus to password field."""
        self.password_input.setFocus()
    
    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.locked_label.setVisible(False)
    
    def _show_locked(self, message: str):
        """Display account locked indicator."""
        self.locked_label.setText(f"🔒 {message}")
        self.locked_label.setVisible(True)
        self.error_label.setVisible(False)
    
    def _clear_status(self):
        """Clear all status messages."""
        self.error_label.setVisible(False)
        self.locked_label.setVisible(False)
    
    def _attempt_login(self):
        """Attempt to authenticate user."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validate input
        if not username:
            self._show_error("Please enter your username")
            self.username_input.setFocus()
            return
        
        if not password:
            self._show_error("Please enter your password")
            self.password_input.setFocus()
            return
        
        # Clear previous status
        self._clear_status()
        
        # Disable login button during authentication
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")
        QApplication.processEvents()
        
        # Attempt authentication
        success, message = self._auth_manager.authenticate(username, password)
        
        # Re-enable login button
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign In")
        
        if success:
            self.login_successful.emit()
            self.accept()
        else:
            # Check if account is locked
            if "locked" in message.lower():
                self._show_locked(message)
            else:
                self._show_error(message)
            
            # Clear password field on failure
            self.password_input.clear()
            self.password_input.setFocus()
    
    def _exit_app(self):
        """Exit the application."""
        self.reject()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Allow Escape to close dialog
        if event.key() == Qt.Key.Key_Escape:
            self._exit_app()
        else:
            super().keyPressEvent(event)


def show_login_dialog() -> bool:
    """
    Show login dialog and return True if login successful.
    
    Returns:
        True if user logged in successfully, False otherwise
    """
    dialog = LoginDialog()
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted


if __name__ == "__main__":
    # Test the dialog
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    result = dialog.exec()
    print(f"Dialog result: {result}")
