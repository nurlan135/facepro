import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGroupBox
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from src.ui.styles import COLORS
from src.utils.i18n import tr
from src.utils.helpers import get_app_root


class SidebarWidget(QWidget):
    """Dashboard Sidebar with profile, menu buttons and stats."""
    
    # Signals for button clicks
    manage_faces_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    user_management_clicked = pyqtSignal()
    change_password_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "sidebar")
        self.setFixedWidth(280)
        
        self._setup_ui()
    
    def _create_sidebar_btn(self, text, icon_path):
        """Helper to create consistent sidebar buttons with icons."""
        btn = QPushButton(text)
        btn.setProperty("class", "sidebar_btn")
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(24, 24))
        return btn
    
    def _setup_ui(self):
        """Setup sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(15)
        
        # Icon Paths
        assets_dir = os.path.join(get_app_root(), 'assets', 'icons')
        icon_profile = os.path.join(assets_dir, 'icon_profile.png')
        icon_faces = os.path.join(assets_dir, 'icon_faces.png')
        icon_settings = os.path.join(assets_dir, 'icon_settings.png')
        icon_users = os.path.join(assets_dir, 'icon_users_mgmt.png')
        icon_password = os.path.join(assets_dir, 'icon_password.png')
        icon_logout = os.path.join(assets_dir, 'icon_logout.png')
        icon_exit = os.path.join(assets_dir, 'icon_exit.png')
        
        # App Title
        title = QLabel("FacePro")
        title.setProperty("class", "sidebar_title")
        layout.addWidget(title)
        
        # Profile Card
        profile_card = QFrame()
        profile_card.setProperty("class", "profile_card")
        pc_layout = QVBoxLayout(profile_card)
        
        # User Icon
        icon_lbl = QLabel()
        if os.path.exists(icon_profile):
            pixmap = QPixmap(icon_profile)
            icon_lbl.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            icon_lbl.setText("👤")
            icon_lbl.setStyleSheet(f"font-size: 40px; color: {COLORS['text_secondary']};")
        
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pc_layout.addWidget(icon_lbl)
        
        # User Name (will be updated with actual username)
        self.admin_lbl = QLabel(tr('sidebar_admin'))
        self.admin_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.admin_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pc_layout.addWidget(self.admin_lbl)
        
        # Role Badge - Removed to match target design (Name -> Status Pill)
        # self.role_lbl = QLabel("Admin")
        # self.role_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        # self.role_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # pc_layout.addWidget(self.role_lbl)
        
        # Active Status Badge
        self.status_btn = QPushButton(f"• {tr('sidebar_active')}")
        self.status_btn.setProperty("class", "status_btn_active")
        self.status_btn.setFixedWidth(100)
        self.status_btn.setEnabled(False)
        
        status_container = QWidget()
        s_layout = QHBoxLayout(status_container)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.addWidget(self.status_btn)
        s_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pc_layout.addWidget(status_container)
        
        layout.addWidget(profile_card)
        layout.addSpacing(20)
        
        # Menu Buttons - Admin only buttons
        self.btn_manage = self._create_sidebar_btn(tr('sidebar_manage_faces'), icon_faces)
        self.btn_manage.clicked.connect(self.manage_faces_clicked.emit)
        layout.addWidget(self.btn_manage)
        
        self.btn_settings = self._create_sidebar_btn(tr('sidebar_settings'), icon_settings)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.btn_settings)
        
        # User Management Button (Admin only)
        self.btn_user_mgmt = self._create_sidebar_btn(tr('sidebar_user_management'), icon_users)
        self.btn_user_mgmt.clicked.connect(self.user_management_clicked.emit)
        layout.addWidget(self.btn_user_mgmt)
        
        # Change Password Button (All users)
        self.btn_change_pwd = self._create_sidebar_btn(tr('sidebar_change_password'), icon_password)
        self.btn_change_pwd.clicked.connect(self.change_password_clicked.emit)
        layout.addWidget(self.btn_change_pwd)
        
        layout.addStretch()
        
        # Statistics Section (Cleaner, no GroupBox)
        stats_container = QWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setContentsMargins(10, 0, 10, 0)
        stats_layout.setSpacing(5)
        
        # Section Title
        self.stats_title = QLabel(f"📊 {tr('sidebar_statistics')}")
        self.stats_title.setProperty("class", "sidebar_section_title")
        stats_layout.addWidget(self.stats_title)
        
        # Stats box style
        self.stat_faces_label = QLabel(f"{tr('sidebar_registered_faces')}: 0")
        self.stat_faces_label.setProperty("class", "stat_label")
        
        self.stat_detections_label = QLabel(f"{tr('sidebar_total_detections')}: 0")
        self.stat_detections_label.setProperty("class", "stat_label")
        
        stats_layout.addWidget(self.stat_faces_label)
        stats_layout.addWidget(self.stat_detections_label)
        
        layout.addWidget(stats_container)
        layout.addSpacing(10)
        
        # Logout Button
        self.btn_logout = self._create_sidebar_btn(tr('sidebar_logout'), icon_logout)
        self.btn_logout.clicked.connect(self.logout_clicked.emit)
        layout.addWidget(self.btn_logout)
        
        # Exit Button
        self.btn_exit = self._create_sidebar_btn(tr('sidebar_exit'), icon_exit)
        self.btn_exit.setProperty("class", "logout_btn")
        self.btn_exit.clicked.connect(self.exit_clicked.emit)
        layout.addWidget(self.btn_exit)
    
    def update_stats(self, faces_count: int, detections_count: int):
        """Update statistics display."""
        self.stat_faces_label.setText(f"{tr('sidebar_registered_faces')}: {faces_count}")
        self.stat_detections_label.setText(f"{tr('sidebar_total_detections')}: {detections_count}")
    
    def set_user_info(self, username: str, role: str):
        """
        Update sidebar with current user info.
        
        Args:
            username: Current user's username
            role: User role ('admin' or 'operator')
        """
        self.admin_lbl.setText(username)
        # self.role_lbl.setText(role.capitalize())
        
        # Apply role-based visibility
        is_admin = role == 'admin'
        
        # Hide/disable admin-only features for operators
        self.btn_manage.setVisible(is_admin)
        self.btn_settings.setVisible(is_admin)
        self.btn_user_mgmt.setVisible(is_admin)
        
        # Change password is available to all users
        self.btn_change_pwd.setVisible(True)
    
    def update_language(self):
        """Update all text for live language change."""
        # Don't override username with translation
        self.status_btn.setText(f"• {tr('sidebar_active')}")
        self.btn_manage.setText(tr('sidebar_manage_faces'))
        self.btn_settings.setText(tr('sidebar_settings'))
        self.btn_user_mgmt.setText(tr('sidebar_user_management'))
        self.btn_change_pwd.setText(tr('sidebar_change_password'))
        self.btn_logout.setText(tr('sidebar_logout'))
        self.stats_title.setText(f"📊 {tr('sidebar_statistics')}")
        self.btn_exit.setText(tr('sidebar_exit'))
