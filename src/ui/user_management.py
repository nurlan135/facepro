"""
FacePro User Management Dialog Module
Admin interface for managing user accounts.

Requirements: 3.1, 3.2, 3.3, 3.4
- Display list of all users with username, role, created_at
- Add User button → opens add dialog
- Edit button → opens edit dialog
- Delete button with confirmation
"""

import os
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QMessageBox, QWidget, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.auth_manager import get_auth_manager
from src.utils.i18n import tr
from src.ui.styles import COLORS, CYBER_THEME


# User Management Dialog Style - Cyber Brutalist Theme
USER_MANAGEMENT_STYLE = f"""
QDialog {{
    background-color: {COLORS.get('bg_panel', '#050505')};
    color: {COLORS.get('text_main', '#e0e0e0')};
    border: 1px solid {COLORS.get('border_tech', '#333')};
}}

QLabel {{
    color: {COLORS.get('text_main', '#e0e0e0')};
    font-family: 'Segoe UI', sans-serif;
}}

QLabel#Title {{
    color: {COLORS.get('cyber_cyan', '#00f0ff')};
    font-family: 'Rajdhani', sans-serif;
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QLabel#Subtitle {{
    color: {COLORS.get('text_muted', '#bbb')};
    font-size: 13px;
    font-style: italic;
}}

QLabel#FieldLabel {{
    color: {COLORS.get('text_muted', '#aaa')};
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel#ErrorLabel {{
    color: {COLORS.get('alert_red', '#ff003c')};
    font-size: 13px;
    padding: 8px;
    background-color: rgba(255, 0, 60, 0.1);
    border-left: 2px solid {COLORS.get('alert_red', '#ff003c')};
}}

QLabel#SuccessLabel {{
    color: {COLORS.get('acid_green', '#00ff00')};
    font-size: 13px;
    padding: 8px;
    background-color: rgba(0, 255, 0, 0.1);
    border-left: 2px solid {COLORS.get('acid_green', '#00ff00')};
}}

QLineEdit {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {COLORS.get('text_main', '#fff')};
    border: 1px solid {COLORS.get('border_tech', '#333')};
    border-radius: 2px;
    padding: 8px 12px;
    font-family: 'Consolas', monospace;
    font-size: 14px;
    selection-background-color: {COLORS.get('cyber_cyan', '#00f0ff')};
    selection-color: black;
}}

QLineEdit:focus {{
    border: 1px solid {COLORS.get('cyber_cyan', '#00f0ff')};
    background-color: rgba(0, 240, 255, 0.05);
}}

QLineEdit:disabled {{
    background-color: rgba(255, 255, 255, 0.02);
    color: {COLORS.get('text_muted', '#666')};
    border: 1px dashed {COLORS.get('border_tech', '#333')};
}}

QComboBox {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {COLORS.get('text_main', '#fff')};
    border: 1px solid {COLORS.get('border_tech', '#333')};
    border-radius: 2px;
    padding: 8px 12px;
    font-family: 'Consolas', monospace;
    min-width: 120px;
}}

QComboBox:focus {{
    border: 1px solid {COLORS.get('cyber_cyan', '#00f0ff')};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS.get('bg_panel', '#050505')};
    color: {COLORS.get('text_main', '#fff')};
    border: 1px solid {COLORS.get('cyber_cyan', '#00f0ff')};
    selection-background-color: {COLORS.get('cyber_cyan', '#00f0ff')};
    selection-color: black;
}}

/* Buttons */
QPushButton {{
    border-radius: 2px;
    padding: 8px 20px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 14px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QPushButton#AddBtn {{
    background-color: {COLORS.get('acid_green', '#00ff00')};
    color: black;
    border: none;
}}

QPushButton#AddBtn:hover {{
    background-color: #b3ff00;
    color: black;
}}

QPushButton#EditBtn {{
    background-color: transparent;
    color: {COLORS.get('cyber_cyan', '#00f0ff')};
    border: 1px solid {COLORS.get('cyber_cyan', '#00f0ff')};
}}

QPushButton#EditBtn:hover {{
    background-color: rgba(0, 240, 255, 0.1);
    color: {COLORS.get('cyber_cyan', '#00f0ff')};
}}

QPushButton#DeleteBtn {{
    background-color: transparent;
    color: {COLORS.get('alert_red', '#ff003c')};
    border: 1px solid {COLORS.get('alert_red', '#ff003c')};
}}

QPushButton#DeleteBtn:hover {{
    background-color: rgba(255, 0, 60, 0.1);
    color: {COLORS.get('alert_red', '#ff003c')};
}}

QPushButton#CloseBtn, QPushButton#CancelBtn {{
    background-color: transparent;
    color: {COLORS.get('text_muted', '#888')};
    border: 1px solid {COLORS.get('border_tech', '#444')};
}}

QPushButton#CloseBtn:hover, QPushButton#CancelBtn:hover {{
    border-color: {COLORS.get('text_main', '#fff')};
    color: {COLORS.get('text_main', '#fff')};
}}

QPushButton#SaveBtn {{
    background-color: {COLORS.get('cyber_cyan', '#00f0ff')};
    color: black;
    border: none;
}}

QPushButton#SaveBtn:hover {{
    background-color: #00d0e0;
}}

QPushButton:disabled {{
    background-color: transparent;
    color: #444;
    border: 1px solid #333;
}}

/* Table Widget */
QTableWidget {{
    background-color: transparent;
    color: {COLORS.get('text_main', '#e0e0e0')};
    border: 1px solid {COLORS.get('border_tech', '#333')};
    border-radius: 0px;
    gridline-color: {COLORS.get('grid_line', '#222')};
    font-family: 'Consolas', monospace;
    font-size: 13px;
    outline: none;
}}

QTableWidget::item:focus {{
    outline: none;
    border: none;
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS.get('grid_line', '#222')};
}}

QTableWidget::item:selected {{
    background-color: rgba(0, 240, 255, 0.2);
    color: white;
    border: 1px solid {COLORS.get('cyber_cyan', '#00f0ff')};
}}

QTableWidget::item:hover {{
    background-color: rgba(255, 255, 255, 0.05);
}}

QHeaderView::section {{
    background-color: {COLORS.get('bg_panel', '#0a0a0a')};
    color: {COLORS.get('cyber_cyan', '#00f0ff')};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {COLORS.get('cyber_cyan', '#00f0ff')};
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 1px;
}}

/* Divider */
QFrame#Divider {{
    background-color: {COLORS.get('cyber_cyan', '#00f0ff')};
    max-height: 2px;
}}

QMessageBox {{
    background-color: {COLORS.get('bg_panel', '#050505')};
}}

QMessageBox QLabel {{
    color: {COLORS.get('text_main', '#fff')};
}}

QMessageBox QPushButton {{
    background: transparent;
    border: 1px solid {COLORS.get('border_tech', '#555')};
    color: #fff;
    padding: 5px 15px;
}}
"""


class AddUserDialog(QDialog):
    """
    Dialog for adding a new user account.
    
    Requirements: 3.2
    - Allow setting username, password, and role (Admin or Operator)
    """
    
    user_added = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth_manager = get_auth_manager()
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(tr("add_user_title"))
        self.setFixedSize(400, 380)
        self.setStyleSheet(USER_MANAGEMENT_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel(tr("add_user_title").upper())
        title.setObjectName("Title")
        layout.addWidget(title)
        
        # Form
        self._create_form(layout)
        
        # Status area
        self._create_status_area(layout)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))
        
        # Buttons
        self._create_buttons(layout)
        
        self.username_input.setFocus()
    
    def _create_form(self, layout: QVBoxLayout):
        """Create form fields."""
        # Username
        username_layout = QVBoxLayout()
        username_layout.setSpacing(4)
        username_label = QLabel(tr("user_field_username"))
        username_label.setObjectName("FieldLabel")
        username_layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(tr("user_placeholder_username"))
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Password
        password_layout = QVBoxLayout()
        password_layout.setSpacing(4)
        password_label = QLabel(tr("user_field_password"))
        password_label.setObjectName("FieldLabel")
        password_layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(tr("user_placeholder_password"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # Role
        role_layout = QVBoxLayout()
        role_layout.setSpacing(4)
        role_label = QLabel(tr("user_field_role"))
        role_label.setObjectName("FieldLabel")
        role_layout.addWidget(role_label)
        self.role_combo = QComboBox()
        self.role_combo.addItems([tr("user_mgmt_role_operator"), tr("user_mgmt_role_admin")])
        role_layout.addWidget(self.role_combo)
        layout.addLayout(role_layout)
    
    def _create_status_area(self, layout: QVBoxLayout):
        """Create status message area."""
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
    
    def _create_buttons(self, layout: QVBoxLayout):
        """Create action buttons."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton(tr("user_btn_cancel").upper())
        cancel_btn.setObjectName("CancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton(tr("user_btn_add").upper())
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._add_user)
        btn_layout.addWidget(self.save_btn, 1)
        
        layout.addLayout(btn_layout)
    
    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
    
    def _add_user(self):
        """Add the new user."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        # Get role value (convert display text back to lowercase)
        role_text = self.role_combo.currentText()
        role = "admin" if role_text == tr("user_mgmt_role_admin") else "operator"
        
        if len(username) < 3:
            self._show_error(tr("user_err_username_short"))
            return
        
        if len(password) < 6:
            self._show_error(tr("user_err_password_short"))
            return
        
        self.save_btn.setEnabled(False)
        self.save_btn.setText(tr("user_adding"))
        QApplication.processEvents()
        
        success, message = self._auth_manager.create_account(username, password, role)
        
        if success:
            self.user_added.emit()
            self.accept()
        else:
            self._show_error(message)
            self.save_btn.setEnabled(True)
            self.save_btn.setText(tr("user_btn_add"))


class EditUserDialog(QDialog):
    """
    Dialog for editing an existing user account.
    
    Requirements: 3.3
    - Allow changing password and role
    """
    
    user_updated = pyqtSignal()
    
    def __init__(self, user_id: int, username: str, current_role: str, parent=None):
        super().__init__(parent)
        self._auth_manager = get_auth_manager()
        self._user_id = user_id
        self._username = username
        self._current_role = current_role
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(tr("edit_user_title"))
        self.setFixedSize(400, 380)
        self.setStyleSheet(USER_MANAGEMENT_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel(f"{tr('edit_user_title').upper()}: {self._username}")
        title.setObjectName("Title")
        layout.addWidget(title)
        
        # Form
        self._create_form(layout)
        
        # Status area
        self._create_status_area(layout)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        ))
        
        # Buttons
        self._create_buttons(layout)
    
    def _create_form(self, layout: QVBoxLayout):
        """Create form fields."""
        # Username (read-only)
        username_layout = QVBoxLayout()
        username_layout.setSpacing(4)
        username_label = QLabel(tr("user_field_username"))
        username_label.setObjectName("FieldLabel")
        username_layout.addWidget(username_label)
        username_display = QLineEdit(self._username)
        username_display.setEnabled(False)
        username_layout.addWidget(username_display)
        layout.addLayout(username_layout)
        
        # New Password (optional)
        password_layout = QVBoxLayout()
        password_layout.setSpacing(4)
        password_label = QLabel(tr("user_field_new_password"))
        password_label.setObjectName("FieldLabel")
        password_layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(tr("user_placeholder_new_password"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # Role
        role_layout = QVBoxLayout()
        role_layout.setSpacing(4)
        role_label = QLabel(tr("user_field_role"))
        role_label.setObjectName("FieldLabel")
        role_layout.addWidget(role_label)
        self.role_combo = QComboBox()
        self.role_combo.addItems([tr("user_mgmt_role_operator"), tr("user_mgmt_role_admin")])
        # Set current role
        index = 1 if self._current_role == 'admin' else 0
        self.role_combo.setCurrentIndex(index)
        role_layout.addWidget(self.role_combo)
        layout.addLayout(role_layout)
    
    def _create_status_area(self, layout: QVBoxLayout):
        """Create status message area."""
        self.error_label = QLabel("")
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
    
    def _create_buttons(self, layout: QVBoxLayout):
        """Create action buttons."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton(tr("user_btn_cancel").upper())
        cancel_btn.setObjectName("CancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton(tr("user_btn_save").upper())
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save_changes)
        btn_layout.addWidget(self.save_btn, 1)
        
        layout.addLayout(btn_layout)
    
    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
    
    def _save_changes(self):
        """Save the user changes."""
        password = self.password_input.text()
        # Get role value (convert display text back to lowercase)
        role_text = self.role_combo.currentText()
        role = "admin" if role_text == tr("user_mgmt_role_admin") else "operator"
        
        # Validate password if provided
        if password and len(password) < 6:
            self._show_error(tr("user_err_password_short"))
            return
        
        self.save_btn.setEnabled(False)
        self.save_btn.setText(tr("user_saving"))
        QApplication.processEvents()
        
        # Update account
        password_to_update = password if password else None
        role_to_update = role if role != self._current_role else None
        
        # Only update if something changed
        if password_to_update is None and role_to_update is None:
            self.accept()
            return
        
        success, message = self._auth_manager.update_account(
            self._user_id, 
            password=password_to_update, 
            role=role if role != self._current_role else self._current_role
        )
        
        if success:
            self.user_updated.emit()
            self.accept()
        else:
            self._show_error(message)
            self.save_btn.setEnabled(True)
            self.save_btn.setText(tr("user_btn_save"))


class UserManagementDialog(QDialog):
    """
    User management dialog for administrators.
    
    Features:
    - Table showing all users (username, role, created_at)
    - Add User button → opens add dialog
    - Edit button → opens edit dialog
    - Delete button with confirmation
    
    Requirements: 3.1, 3.2, 3.3, 3.4
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth_manager = get_auth_manager()
        self._setup_ui()
        self._load_users()
    
    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(tr("user_mgmt_title"))
        self.setMinimumSize(700, 500)
        self.setStyleSheet(USER_MANAGEMENT_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        self._create_header(layout)
        
        # Divider
        divider = QFrame()
        divider.setObjectName("Divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)
        
        # User table
        self._create_table(layout)
        
        # Action buttons
        self._create_action_buttons(layout)
        
        # Footer buttons
        self._create_footer_buttons(layout)
    
    def _create_header(self, layout: QVBoxLayout):
        """Create header with title and subtitle."""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        title = QLabel(tr("user_mgmt_title"))
        title.setObjectName("Title")
        header_layout.addWidget(title)
        
        subtitle = QLabel(tr("user_mgmt_subtitle"))
        subtitle.setObjectName("Subtitle")
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
    
    def _create_table(self, layout: QVBoxLayout):
        """Create user table."""
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels([tr("user_mgmt_col_username"), tr("user_mgmt_col_role"), tr("user_mgmt_col_created"), "ID"])
        
        # Hide ID column (used for operations)
        self.user_table.setColumnHidden(3, True)
        
        # Configure table
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.user_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.user_table.setAlternatingRowColors(False)
        self.user_table.verticalHeader().setVisible(False)
        
        # Column sizing
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.user_table.setColumnWidth(1, 100)
        self.user_table.setColumnWidth(2, 150)
        
        # Connect selection change
        self.user_table.itemSelectionChanged.connect(self._on_selection_changed)
        self.user_table.doubleClicked.connect(self._edit_user)
        
        layout.addWidget(self.user_table)
    
    def _create_action_buttons(self, layout: QVBoxLayout):
        """Create action buttons for user operations."""
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # Add User button
        self.add_btn = QPushButton(f"+ {tr('user_mgmt_add').upper()}")
        self.add_btn.setObjectName("AddBtn")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._add_user)
        btn_layout.addWidget(self.add_btn)
        
        # Edit button
        self.edit_btn = QPushButton(tr('user_mgmt_edit').upper())
        self.edit_btn.setObjectName("EditBtn")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._edit_user)
        btn_layout.addWidget(self.edit_btn)
        
        # Delete button
        self.delete_btn = QPushButton(tr("user_mgmt_delete").upper())
        self.delete_btn.setObjectName("DeleteBtn")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._delete_user)
        btn_layout.addWidget(self.delete_btn)
        
        # Spacer
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def _create_footer_buttons(self, layout: QVBoxLayout):
        """Create footer with close button."""
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton(tr("user_mgmt_close").upper())
        close_btn.setObjectName("CloseBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _load_users(self):
        """Load users from database into table."""
        self.user_table.setRowCount(0)
        
        accounts = self._auth_manager.list_accounts()
        
        for account in accounts:
            row = self.user_table.rowCount()
            self.user_table.insertRow(row)
            
            # Username
            username_item = QTableWidgetItem(account.username)
            self.user_table.setItem(row, 0, username_item)
            
            # Role (capitalized)
            role_item = QTableWidgetItem(account.role.capitalize())
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(row, 1, role_item)
            
            # Created date
            created_str = account.created_at.strftime("%Y-%m-%d %H:%M")
            created_item = QTableWidgetItem(created_str)
            created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(row, 2, created_item)
            
            # Hidden ID column
            id_item = QTableWidgetItem(str(account.id))
            self.user_table.setItem(row, 3, id_item)
        
        # Update button states
        self._on_selection_changed()
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        has_selection = len(self.user_table.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def _get_selected_user(self):
        """Get selected user info."""
        selected_rows = self.user_table.selectedItems()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        user_id = int(self.user_table.item(row, 3).text())
        username = self.user_table.item(row, 0).text()
        role = self.user_table.item(row, 1).text().lower()
        
        return {'id': user_id, 'username': username, 'role': role}
    
    def _add_user(self):
        """Open add user dialog."""
        dialog = AddUserDialog(self)
        dialog.user_added.connect(self._load_users)
        dialog.exec()
    
    def _edit_user(self):
        """Open edit user dialog."""
        user = self._get_selected_user()
        if not user:
            return
        
        dialog = EditUserDialog(
            user_id=user['id'],
            username=user['username'],
            current_role=user['role'],
            parent=self
        )
        dialog.user_updated.connect(self._load_users)
        dialog.exec()
    
    def _delete_user(self):
        """Delete selected user with confirmation."""
        user = self._get_selected_user()
        if not user:
            return
        
        # Confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(tr("user_mgmt_confirm_delete"))
        msg_box.setText(f"{tr('user_mgmt_delete_msg')} '{user['username']}'?")
        msg_box.setInformativeText(tr("user_delete_cannot_undo"))
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        # Style the message box
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['bg_dark']};
            }}
            QMessageBox QLabel {{
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QPushButton {{
                min-width: 80px;
                padding: 8px 16px;
            }}
        """)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            success, message = self._auth_manager.delete_account(user['id'])
            
            if success:
                self._load_users()
            else:
                # Show error
                error_box = QMessageBox(self)
                error_box.setWindowTitle(tr("user_error_title"))
                error_box.setText(message)
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setStyleSheet(f"""
                    QMessageBox {{
                        background-color: {COLORS['bg_dark']};
                    }}
                    QMessageBox QLabel {{
                        color: {COLORS['text_primary']};
                    }}
                """)
                error_box.exec()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        elif event.key() == Qt.Key.Key_Delete:
            self._delete_user()
        else:
            super().keyPressEvent(event)


def show_user_management() -> None:
    """
    Show user management dialog.
    """
    dialog = UserManagementDialog()
    dialog.exec()


if __name__ == "__main__":
    # Test the dialog
    app = QApplication(sys.argv)
    dialog = UserManagementDialog()
    dialog.exec()
