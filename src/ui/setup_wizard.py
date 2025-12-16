"""
FacePro Setup Wizard Dialog Module
First-time admin account creation wizard.

Requirements: 1.1, 1.2, 1.4
"""

import os
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QApplication,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QKeyEvent

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.auth_manager import get_auth_manager
from src.utils.i18n import tr
from src.ui.styles import COLORS


SETUP_WIZARD_STYLE = f"""
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
QLabel#WelcomeText {{
    color: {COLORS['text_primary']};
    font-size: 16px;
    font-weight: 500;
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
QLabel#HintLabel {{
    color: {COLORS['text_muted']};
    font-size: 11px;
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
QPushButton {{
    border-radius: 8px;
    padding: 12px 24px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 600;
}}
QPushButton#CreateBtn {{
    background-color: {COLORS['success']};
    color: white;
    border: none;
    font-size: 15px;
    min-height: 20px;
}}
QPushButton#CreateBtn:hover {{
    background-color: #27ae60;
}}
QPushButton#CreateBtn:pressed {{
    background-color: #1e8449;
}}
QPushButton#CreateBtn:disabled {{
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


class SetupWizardDialog(QDialog):
    """Setup wizard dialog for first-time admin account creation."""
    
    setup_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth_manager = get_auth_manager()
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle(tr("setup_title"))
        self.setFixedSize(480, 580)
        self.setStyleSheet(SETUP_WIZARD_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.CustomizeWindowHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(50, 40, 50, 40)
        
        self._create_header(layout)
        
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)
        
        self._create_welcome_message(layout)
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
        
        subtitle = QLabel(tr("setup_subtitle"))
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
    
    def _create_welcome_message(self, layout: QVBoxLayout):
        welcome_text = QLabel(tr("setup_welcome"))
        welcome_text.setObjectName("WelcomeText")
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_text.setWordWrap(True)
        layout.addWidget(welcome_text)
    
    def _create_form(self, layout: QVBoxLayout):
        form_layout = QVBoxLayout()
        form_layout.setSpacing(14)
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(4)
        
        username_label = QLabel(tr("setup_username"))
        username_label.setObjectName("FieldLabel")
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(tr("setup_username_placeholder"))
        self.username_input.textChanged.connect(self._validate_form)
        self.username_input.returnPressed.connect(self._focus_password)
        username_layout.addWidget(self.username_input)
        
        self.username_hint = QLabel("")
        self.username_hint.setObjectName("HintLabel")
        username_layout.addWidget(self.username_hint)
        
        form_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(4)
        
        password_label = QLabel(tr("setup_password"))
        password_label.setObjectName("FieldLabel")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(tr("setup_password_placeholder"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.textChanged.connect(self._validate_form)
        self.password_input.returnPressed.connect(self._focus_confirm)
        password_layout.addWidget(self.password_input)
        
        self.password_hint = QLabel("")
        self.password_hint.setObjectName("HintLabel")
        password_layout.addWidget(self.password_hint)
        
        form_layout.addLayout(password_layout)
        
        # Confirm Password field
        confirm_layout = QVBoxLayout()
        confirm_layout.setSpacing(4)
        
        confirm_label = QLabel(tr("setup_confirm"))
        confirm_label.setObjectName("FieldLabel")
        confirm_layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText(tr("setup_confirm_placeholder"))
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.textChanged.connect(self._validate_form)
        self.confirm_input.returnPressed.connect(self._attempt_create)
        confirm_layout.addWidget(self.confirm_input)
        
        self.confirm_hint = QLabel("")
        self.confirm_hint.setObjectName("HintLabel")
        confirm_layout.addWidget(self.confirm_hint)
        
        form_layout.addLayout(confirm_layout)
        
        layout.addLayout(form_layout)
    
    def _create_status_area(self, layout: QVBoxLayout):
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        self.success_label = QLabel("")
        self.success_label.setObjectName("SuccessLabel")
        self.success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_label.setWordWrap(True)
        self.success_label.setVisible(False)
        layout.addWidget(self.success_label)
    
    def _create_buttons(self, layout: QVBoxLayout):
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        exit_btn = QPushButton(tr("setup_btn_exit"))
        exit_btn.setObjectName("ExitBtn")
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.clicked.connect(self._exit_app)
        btn_layout.addWidget(exit_btn)
        
        self.create_btn = QPushButton(tr("setup_btn_create"))
        self.create_btn.setObjectName("CreateBtn")
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.clicked.connect(self._attempt_create)
        self.create_btn.setEnabled(False)
        btn_layout.addWidget(self.create_btn, 1)
        
        layout.addLayout(btn_layout)
    
    def _focus_password(self):
        self.password_input.setFocus()
    
    def _focus_confirm(self):
        self.confirm_input.setFocus()
    
    def _validate_form(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        is_valid = True
        
        # Validate username
        if len(username) == 0:
            self.username_hint.setText("")
        elif len(username) < 3:
            self.username_hint.setText(tr("setup_hint_username_short"))
            self.username_hint.setStyleSheet(f"color: {COLORS['danger']};")
            is_valid = False
        else:
            self.username_hint.setText("✓ " + tr("setup_hint_username_valid"))
            self.username_hint.setStyleSheet(f"color: {COLORS['success']};")
        
        # Validate password
        if len(password) == 0:
            self.password_hint.setText("")
        elif len(password) < 6:
            self.password_hint.setText(tr("setup_hint_password_short"))
            self.password_hint.setStyleSheet(f"color: {COLORS['danger']};")
            is_valid = False
        else:
            self.password_hint.setText("✓ " + tr("setup_hint_password_valid"))
            self.password_hint.setStyleSheet(f"color: {COLORS['success']};")
        
        # Validate confirm password
        if len(confirm) == 0:
            self.confirm_hint.setText("")
        elif confirm != password:
            self.confirm_hint.setText(tr("setup_hint_password_mismatch"))
            self.confirm_hint.setStyleSheet(f"color: {COLORS['danger']};")
            is_valid = False
        elif len(password) >= 6:
            self.confirm_hint.setText("✓ " + tr("setup_hint_password_match"))
            self.confirm_hint.setStyleSheet(f"color: {COLORS['success']};")
        
        all_filled = len(username) >= 3 and len(password) >= 6 and len(confirm) >= 6
        passwords_match = password == confirm
        
        self.create_btn.setEnabled(all_filled and passwords_match and is_valid)
    
    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        self.success_label.setVisible(False)
    
    def _show_success(self, message: str):
        self.success_label.setText(message)
        self.success_label.setVisible(True)
        self.error_label.setVisible(False)
    
    def _clear_status(self):
        self.error_label.setVisible(False)
        self.success_label.setVisible(False)
    
    def _attempt_create(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if len(username) < 3:
            self._show_error(tr("setup_hint_username_short"))
            self.username_input.setFocus()
            return
        
        if len(password) < 6:
            self._show_error(tr("setup_hint_password_short"))
            self.password_input.setFocus()
            return
        
        if password != confirm:
            self._show_error(tr("setup_hint_password_mismatch"))
            self.confirm_input.setFocus()
            return
        
        self._clear_status()
        
        self.create_btn.setEnabled(False)
        self.create_btn.setText(tr("setup_creating"))
        QApplication.processEvents()
        
        success, message = self._auth_manager.create_account(username, password, 'admin')
        
        if success:
            self._show_success("✓ " + tr("setup_success"))
            QApplication.processEvents()
            QTimer.singleShot(1000, self._complete_setup)
        else:
            self._show_error(message)
            self.create_btn.setEnabled(True)
            self.create_btn.setText(tr("setup_btn_create"))
    
    def _complete_setup(self):
        self.setup_completed.emit()
        self.accept()
    
    def _exit_app(self):
        self.reject()
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self._exit_app()
        else:
            super().keyPressEvent(event)


def show_setup_wizard() -> bool:
    dialog = SetupWizardDialog()
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SetupWizardDialog()
    result = dialog.exec()
    print(f"Dialog result: {result}")
