"""
FacePro Dashboard Sidebar
Left sidebar with profile, navigation and stats.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.styles import COLORS
from src.utils.i18n import tr


class SidebarWidget(QWidget):
    """Dashboard Sidebar with profile, menu buttons and stats."""
    
    # Signals for button clicks
    manage_faces_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    exit_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "sidebar")
        self.setFixedWidth(280)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 30, 20, 30)
        layout.setSpacing(15)
        
        # App Title
        title = QLabel("FacePro")
        title.setProperty("class", "sidebar_title")
        layout.addWidget(title)
        
        # Profile Card
        profile_card = QFrame()
        profile_card.setProperty("class", "profile_card")
        pc_layout = QVBoxLayout(profile_card)
        
        # User Icon
        icon_lbl = QLabel("👤")
        icon_lbl.setStyleSheet(f"font-size: 40px; color: {COLORS['text_secondary']};")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pc_layout.addWidget(icon_lbl)
        
        # User Name
        self.admin_lbl = QLabel(tr('sidebar_admin'))
        self.admin_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.admin_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pc_layout.addWidget(self.admin_lbl)
        
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
        
        # Menu Buttons
        self.btn_manage = QPushButton(f"👥  {tr('sidebar_manage_faces')}")
        self.btn_manage.setProperty("class", "sidebar_btn")
        self.btn_manage.clicked.connect(self.manage_faces_clicked.emit)
        layout.addWidget(self.btn_manage)
        
        self.btn_settings = QPushButton(f"⚙  {tr('sidebar_settings')}")
        self.btn_settings.setProperty("class", "sidebar_btn")
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.btn_settings)
        
        layout.addStretch()
        
        # Statistics Widget
        self.stats_group = QGroupBox(f"📊 {tr('sidebar_statistics')}")
        stats_layout = QVBoxLayout()
        self.stat_faces_label = QLabel(f"{tr('sidebar_registered_faces')}: --")
        self.stat_detections_label = QLabel(f"{tr('sidebar_total_detections')}: --")
        
        stats_layout.addWidget(self.stat_faces_label)
        stats_layout.addWidget(self.stat_detections_label)
        self.stats_group.setLayout(stats_layout)
        layout.addWidget(self.stats_group)
        
        layout.addSpacing(10)
        
        # Logout / Exit Button
        self.btn_exit = QPushButton(f"🚪 {tr('sidebar_exit')}")
        self.btn_exit.setProperty("class", "logout_btn")
        self.btn_exit.clicked.connect(self.exit_clicked.emit)
        layout.addWidget(self.btn_exit)
    
    def update_stats(self, faces_count: int, detections_count: int):
        """Update statistics display."""
        self.stat_faces_label.setText(f"{tr('sidebar_registered_faces')}: {faces_count}")
        self.stat_detections_label.setText(f"{tr('sidebar_total_detections')}: {detections_count}")
    
    def update_language(self):
        """Update all text for live language change."""
        self.admin_lbl.setText(tr('sidebar_admin'))
        self.status_btn.setText(f"• {tr('sidebar_active')}")
        self.btn_manage.setText(f"👥  {tr('sidebar_manage_faces')}")
        self.btn_settings.setText(f"⚙  {tr('sidebar_settings')}")
        self.stats_group.setTitle(f"📊 {tr('sidebar_statistics')}")
        self.btn_exit.setText(f"🚪 {tr('sidebar_exit')}")
