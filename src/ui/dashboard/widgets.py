"""
FacePro Dashboard Widgets
Custom widgets for dashboard UI.
"""

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
import os

from src.ui.styles import COLORS


class ActivityItem(QWidget):
    """Activity Feed Item (for recent detections)."""
    
    def __init__(self, name: str, time_str: str, is_known: bool = True, 
                 camera_name: str = "", parent=None):
        super().__init__(parent)
        self.is_known = is_known
        self.setMinimumHeight(60)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(15)
        
        # 1. Status/Icon Box
        # This creates the green outlined box with the checkmark seen in the design
        status_box = QFrame()
        status_box.setFixedSize(40, 40)
        
        if is_known:
            status_box.setProperty("class", "activity_icon_box_success")
            icon_text = "✔"
        else:
            status_box.setProperty("class", "activity_icon_box_warning")
            icon_text = "?"
            
        sb_layout = QVBoxLayout(status_box)
        sb_layout.setContentsMargins(0,0,0,0)
        sb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel(icon_text)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sb_layout.addWidget(icon_lbl)
        
        layout.addWidget(status_box)
        
        # 2. Name and Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        name_lbl = QLabel(name)
        # Using a class for easy styling of the name
        name_lbl.setProperty("class", "activity_name")
        info_layout.addWidget(name_lbl)
        
        if camera_name:
            camera_lbl = QLabel(camera_name) # Icon removed from text to be cleaner
            camera_lbl.setProperty("class", "activity_detail")
            info_layout.addWidget(camera_lbl)
            
        layout.addLayout(info_layout, 1)
        
        # 3. Time
        time_lbl = QLabel(time_str)
        time_lbl.setProperty("class", "activity_time")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(time_lbl)


class ActionCard(QFrame):
    """Large Action Card (Dashboard Button)."""
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str, subtitle: str, icon_source: str, parent=None, is_path: bool = False):
        super().__init__(parent)
        self.setProperty("class", "action_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(180)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        # Icon
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if is_path and os.path.exists(icon_source):
             pixmap = QPixmap(icon_source)
             scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
             icon_lbl.setPixmap(scaled_pixmap)
        else:
            icon_lbl.setText(icon_source)
            icon_lbl.setStyleSheet(f"font-size: 48px; color: {COLORS['text_primary']};")
            
        layout.addWidget(icon_lbl)
        
        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['text_primary']};")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_lbl)
        
        # Subtitle
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        self.sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.sub_lbl)
    
    def update_text(self, title: str, subtitle: str):
        """Update card text (for live language change)."""
        self.title_lbl.setText(title)
        self.sub_lbl.setText(subtitle)
        
    def mousePressEvent(self, event):
        self.clicked.emit()
