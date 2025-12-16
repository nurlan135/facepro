"""
FacePro Change Password Dialog Module
User interface for changing account password.

Requirements: 5.1, 5.4
- Current password field for verification
- New password + Confirm fields
- Validation and success/error feedback
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


# Change Password Dialog Style - Dark theme consistent with app
CHANGE_PASSWORD_STYLE = f"""
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
    font-size: 24px;
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

QLabel#SuccessLabel {{
    color: {COLORS['success']};
    font-size: 13px;
    font-weight: 500;
    padding: 8px;
    background-color: rgba(46, 204, 113, 0.1);
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

QPushButton#SaveBtn {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    min-height: 20px;
}}

QPushButton#SaveBtn:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton#SaveBtn:pressed {{
    background-color: #1d4ed8;
}}

QPushButton#SaveBtn:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_muted']};
}}

QPushButton#CancelBtn {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
}}

QPushButton#CancelBtn:hover {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border-color: {COLORS['border_light']};
}}

QFrame#Divider {{
    background-color: {COLORS['border']};
    max-height: 1px;
}}
"""


class ChangePasswordDialog(QDialog):
    """
    Dialog for changing user password.
    
    Features:
    - Dark theme consistent with main application
    - Current password field for verification
    - New password + Confirm fields
    - Validation and success/error feedback
    
    Signals:
        password_changed: Emitted when password is successfully changed
        
    Requirements: 5.1, 5.4
    """
    
    password_changed = pyqtSignal()
    
    def __init__(self, user_id: int = None, parent=None):
        super().__init__(parent)
        self._auth_manager = get_auth_manager()
        self._user_id = user_id  # Optional: if not provided, uses current user
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Change Password")
        self.setFixedSize(440, 480)
        self.setStyleSheet(CHANGE_PASSWORD_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 35, 40, 35)
        
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
        
        # Set focus to current password field
        self.current_password_input.setFocus()
    
    def _create_header(self, layout: QVBoxLayout):
        """Create header with title and subtitle."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Title
        title_label = QLabel("Change Password")
        title_label.setObjectName("Title")
        header_layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("Enter your current password and choose a new one")
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
    
    def _create_form(self, layout: QVBoxLayout):
        """Create password change form with current, new, and confirm fields."""
        form_layout = QVBoxLayout()
        form_layout.setSpacing(16)
        
        # Current password field
        current_layout = QVBoxLayout()
        current_layout.setSpacing(6)
        
        current_label = QLabel("Current Password")
        current_label.setObjectName("FieldLabel")
        current_layout.addWidget(current_label)
        
        self.current_password_input = QLineEdit()
        self.current_password_input.setPlaceholderText("Enter your current password")
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.returnPressed.connect(self._focus_new_password)
        current_layout.addWidget(self.current_password_input)
        
        form_layout.addLayout(current_layout)
        
        # New password field
        new_layout = QVBoxLayout()
        new_layout.setSpacing(6)
        
        new_label = QLabel("New Password")
        new_label.setObjectName("FieldLabel")
        new_layout.addWidget(new_label)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Enter new password (min 6 characters)")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.returnPressed.connect(self._focus_confirm_password)
        new_layout.addWidget(self.new_password_input)
        
        form_layout.addLayout(new_layout)
        
        # Confirm password field
        confirm_layout = QVBoxLayout()
        confirm_layout.setSpacing(6)
        
        confirm_label = QLabel("Confirm New Password")
        confirm_label.setObjectName("FieldLabel")
        confirm_layout.addWidget(confirm_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Re-enter new password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.returnPressed.connect(self._change_password)
        confirm_layout.addWidget(self.confirm_password_input)
        
        form_layout.addLayout(confirm_layout)
        
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
        
        # Success label (hidden by default)
        self.success_label = QLabel("")
        self.success_label.setObjectName("SuccessLabel")
        self.success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_label.setWordWrap(True)
        self.success_label.setVisible(False)
        layout.addWidget(self.success_label)
    
    def _create_buttons(self, layout: QVBoxLayout):
        """Create save and cancel buttons."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("CancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        # Save button
        self.save_btn = QPushButton("Change Password")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._change_password)
        btn_layout.addWidget(self.save_btn, 1)  # Stretch factor
        
        layout.addLayout(btn_layout)
    
    def _focus_new_password(self):
        """Move focus to new password field."""
        self.new_password_input.setFocus()
    
    def _focus_confirm_password(self):
        """Move focus to confirm password field."""
        self.confirm_password_input.setFocus()
    
    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.success_label.setVisible(False)
    
    def _show_success(self, message: str):
        """Display success message."""
        self.success_label.setText(message)
        self.success_label.setVisible(True)
        self.error_label.setVisible(False)
    
    def _clear_status(self):
        """Clear all status messages."""
        self.error_label.setVisible(False)
        self.success_label.setVisible(False)
    
    def _change_password(self):
        """Attempt to change the password."""
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validate input
        if not current_password:
            self._show_error("Please enter your current password")
            self.current_password_input.setFocus()
            return
        
        if not new_password:
            self._show_error("Please enter a new password")
            self.new_password_input.setFocus()
            return
        
        if len(new_password) < 6:
            self._show_error("New password must be at least 6 characters")
            self.new_password_input.setFocus()
            return
        
        if new_password != confirm_password:
            self._show_error("New passwords do not match")
            self.confirm_password_input.setFocus()
            self.confirm_password_input.clear()
            return
        
        if current_password == new_password:
            self._show_error("New password must be different from current password")
            self.new_password_input.setFocus()
            return
        
        # Clear previous status
        self._clear_status()
        
        # Disable save button during operation
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Changing...")
        QApplication.processEvents()
        
        # Get user ID (use provided or current user)
        user_id = self._user_id
        if user_id is None:
            current_user = self._auth_manager.get_current_user()
            if not current_user:
                self._show_error("No user logged in")
                self.save_btn.setEnabled(True)
                self.save_btn.setText("Change Password")
                return
            user_id = current_user.user_id
        
        # Attempt password change
        success, message = self._auth_manager.change_password(
            user_id,
            current_password,
            new_password
        )
        
        if success:
            self._show_success("✓ " + message)
            self.password_changed.emit()
            
            # Clear all fields
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
            
            # Re-enable button with success text
            self.save_btn.setText("Done")
            
            # Close dialog after short delay
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, self.accept)
        else:
            self._show_error(message)
            self.save_btn.setEnabled(True)
            self.save_btn.setText("Change Password")
            
            # Clear current password field on failure
            self.current_password_input.clear()
            self.current_password_input.setFocus()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Allow Escape to close dialog
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)


def show_change_password_dialog() -> bool:
    """
    Show change password dialog and return True if password was changed.
    
    Returns:
        True if password was changed successfully, False otherwise
    """
    dialog = ChangePasswordDialog()
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted


if __name__ == "__main__":
    # Test the dialog
    app = QApplication(sys.argv)
    dialog = ChangePasswordDialog()
    result = dialog.exec()
    print(f"Dialog result: {result}")
