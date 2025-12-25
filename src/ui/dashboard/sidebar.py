"""
FacePro Dashboard Sidebar
Cyber-Brutalist Compact Vertical Navigation
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from src.ui.styles import COLORS
from src.utils.i18n import tr
from src.utils.helpers import get_app_root
from src.ui.components.performance_monitor import PerformanceMonitor

class SidebarWidget(QWidget):
    """
    Compact Vertical Sidebar (Icon-only).
    Matches the 'Cyber-Brutalist' HTML concept.
    """
    
    # Signals
    manage_faces_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    user_management_clicked = pyqtSignal()
    change_password_clicked = pyqtSignal()
    logout_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "sidebar")
        self.setFixedWidth(70) # Compact width
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 15, 5, 15)
        layout.setSpacing(10) # Reduced spacing
        
        # 1. Top Logo / Status Icon
        logo_btn = QPushButton()
        logo_btn.setFixedSize(50, 50)
        logo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 240, 255, 0.1);
                border: 1px solid {COLORS['cyber_cyan']};
                border-radius: 4px;
                color: {COLORS['cyber_cyan']};
                font-size: 24px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 240, 255, 0.2);
            }}
        """)
        # Using a unicode char or icon as logo
        logo_btn.setText("👁") 
        layout.addWidget(logo_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 2. Navigation Buttons (Middle)
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setSpacing(8)
        nav_layout.setContentsMargins(0, 10, 0, 0)
        
        # Icon Paths
        assets_dir = os.path.join(get_app_root(), 'assets', 'icons')
        
        self.btn_manage = self._create_icon_btn("👥", tr("sidebar.manage_faces"), self.manage_faces_clicked)
        nav_layout.addWidget(self.btn_manage)
        
        self.btn_user_mgmt = self._create_icon_btn("🛡", tr("sidebar.user_management"), self.user_management_clicked)
        nav_layout.addWidget(self.btn_user_mgmt)
        
        self.btn_settings = self._create_icon_btn("⚙", tr("sidebar.settings"), self.settings_clicked)
        nav_layout.addWidget(self.btn_settings)
        
        self.btn_pwd = self._create_icon_btn("🔑", tr("sidebar.change_password"), self.change_password_clicked)
        nav_layout.addWidget(self.btn_pwd)
        
        layout.addWidget(nav_container, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        
        # 3. Bottom Actions
        self.btn_logout = self._create_icon_btn("🚪", tr("sidebar.logout"), self.logout_clicked)
        self.btn_logout.setStyleSheet(self.btn_logout.styleSheet().replace(COLORS['cyber_cyan'], COLORS['alert_red']))
        layout.addWidget(self.btn_logout, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # System Stats (Hidden or Minimal)
        # We attach the PerformanceMonitor but keep it invisible or very small 
        # so logic in MainWindow doesn't break
        self.perf_monitor = PerformanceMonitor()
        self.perf_monitor.setVisible(False) 
        layout.addWidget(self.perf_monitor)
        
        # Profile Avatar (Bottom)
        profile_frame = QFrame()
        profile_frame.setFixedSize(40, 40)
        profile_frame.setStyleSheet(f"""
            background: {COLORS['bg_void']}; 
            border: 1px solid {COLORS['cyber_cyan']};
            border-radius: 0px;
        """)
        # We can add a user image later
        layout.addWidget(profile_frame, alignment=Qt.AlignmentFlag.AlignCenter)

    def _create_icon_btn(self, icon_text, tooltip, signal):
        """Creates a stylized icon button."""
        btn = QPushButton(icon_text)
        btn.setProperty("class", "nav_btn")
        btn.setFixedSize(45, 45)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Default style is handled by styles.py ('nav_btn'), 
        # but we can override font size for emoji icons
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: 1px solid transparent;
                font-size: 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: rgba(0, 240, 255, 0.1);
                color: {COLORS['cyber_cyan']};
                border: 1px solid {COLORS['cyber_cyan']};
            }}
        """)
        
        btn.clicked.connect(signal.emit)
        return btn

    def set_user_info(self, username: str, role: str):
        """Update visibility based on role."""
        is_admin = role == 'admin'
        self.btn_manage.setVisible(is_admin)
        self.btn_user_mgmt.setVisible(is_admin)
        self.btn_settings.setVisible(is_admin)
        
        # Update tooltip to show user
        self.btn_logout.setToolTip(f"Logout ({username})")

    def update_stats(self, faces_count, detections_count):
        pass # No space for text stats in compact mode

    def update_language(self):
        self.btn_manage.setToolTip(tr("sidebar.manage_faces"))
        self.btn_user_mgmt.setToolTip(tr("sidebar.user_management"))
        self.btn_settings.setToolTip(tr("sidebar.settings"))
        self.btn_pwd.setToolTip(tr("sidebar.change_password"))
        self.btn_logout.setToolTip(tr("sidebar.logout"))
