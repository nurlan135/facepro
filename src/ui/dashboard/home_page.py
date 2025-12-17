"""
FacePro Dashboard Home Page
Welcome banner, action cards, and activity feed.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QListWidget
)
from PyQt6.QtCore import pyqtSignal

from src.ui.styles import COLORS
from src.utils.i18n import tr
from src.utils.helpers import get_app_root
from .widgets import ActionCard


class HomePage(QWidget):
    """Dashboard Home Page with welcome banner and action cards."""
    
    # Signals for card actions
    start_camera_clicked = pyqtSignal()
    add_face_clicked = pyqtSignal()
    view_logs_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup home page UI."""
        layout = QVBoxLayout(self)
        
        # Welcome Banner
        banner = QFrame()
        banner.setProperty("class", "welcome_banner")
        b_layout = QVBoxLayout(banner)
        
        self.welcome_lbl = QLabel(tr('welcome_title'))
        self.welcome_lbl.setProperty("class", "welcome_text")
        b_layout.addWidget(self.welcome_lbl)
        
        self.tagline_lbl = QLabel(tr('welcome_subtitle'))
        self.tagline_lbl.setProperty("class", "tagline")
        b_layout.addWidget(self.tagline_lbl)
        
        layout.addWidget(banner)
        layout.addSpacing(20)
        
        # Action Cards Row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Icon Paths
        assets_dir = os.path.join(get_app_root(), 'assets', 'icons')
        icon_camera = os.path.join(assets_dir, 'icon_camera.png')
        icon_add_face = os.path.join(assets_dir, 'icon_add_face.png')
        icon_logs = os.path.join(assets_dir, 'icon_logs.png')
        
        # Card 1: Start Camera
        self.card_camera = ActionCard(
            tr('card_start_camera'), 
            tr('card_start_camera_desc'), 
            icon_camera, 
            is_path=True
        )
        self.card_camera.clicked.connect(self.start_camera_clicked.emit)
        cards_layout.addWidget(self.card_camera)
        
        # Card 2: Add Face
        self.card_add_face = ActionCard(
            tr('card_add_face'), 
            tr('card_add_face_desc'), 
            icon_add_face, 
            is_path=True
        )
        self.card_add_face.clicked.connect(self.add_face_clicked.emit)
        cards_layout.addWidget(self.card_add_face)
        
        # Card 3: View Logs
        self.card_view_logs = ActionCard(
            tr('card_view_logs'), 
            tr('card_view_logs_desc'), 
            icon_logs,
            is_path=True
        )
        self.card_view_logs.clicked.connect(self.view_logs_clicked.emit)
        cards_layout.addWidget(self.card_view_logs)
        
        layout.addLayout(cards_layout)
        layout.addSpacing(20)
        
        # Recent Activity Section
        self.recent_activity_lbl = QLabel(f"📄 {tr('recent_activity')}")
        self.recent_activity_lbl.setProperty("class", "sidebar_title")
        layout.addWidget(self.recent_activity_lbl)
        
        self.activity_feed = QListWidget()
        self.activity_feed.setProperty("class", "activity_feed")
        layout.addWidget(self.activity_feed)
    
    def update_language(self):
        """Update all text for live language change."""
        self.welcome_lbl.setText(tr('welcome_title'))
        self.tagline_lbl.setText(tr('welcome_subtitle'))
        self.recent_activity_lbl.setText(f"📄 {tr('recent_activity')}")
        self.card_camera.update_text(tr('card_start_camera'), tr('card_start_camera_desc'))
        self.card_add_face.update_text(tr('card_add_face'), tr('card_add_face_desc'))
        self.card_view_logs.update_text(tr('card_view_logs'), tr('card_view_logs_desc'))
