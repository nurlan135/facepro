"""
FacePro Dashboard Widgets
Custom widgets for dashboard UI.
"""

from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal

from src.ui.styles import COLORS


class ActivityItem(QWidget):
    """Activity Feed Item (for recent detections)."""
    
    def __init__(self, name: str, time_str: str, is_known: bool = True, 
                 camera_name: str = "", parent=None):
        super().__init__(parent)
        self.is_known = is_known  # Store for filtering
        self.setMinimumHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Status Icon
        icon = "✓" if is_known else "⚠"
        icon_color = COLORS['success'] if is_known else COLORS['warning']
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 18px; color: {icon_color}; font-weight: bold;")
        icon_lbl.setFixedWidth(30)
        layout.addWidget(icon_lbl)
        
        # Name and Camera (vertical layout)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"font-size: 14px; color: {COLORS['text_primary']}; font-weight: 500;")
        info_layout.addWidget(name_lbl)
        
        if camera_name:
            camera_lbl = QLabel(f"📷 {camera_name}")
            camera_lbl.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
            info_layout.addWidget(camera_lbl)
        
        layout.addLayout(info_layout, 1)
        
        # Time
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(time_lbl)


class ActionCard(QFrame):
    """Large Action Card (Dashboard Button)."""
    
    clicked = pyqtSignal()
    
    def __init__(self, title: str, subtitle: str, icon_str: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "action_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(180)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        
        # Icon
        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet(f"font-size: 48px; color: {COLORS['text_primary']};")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
