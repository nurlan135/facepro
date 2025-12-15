"""
FacePro Dashboard Camera Page
Video grid and camera controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import pyqtSignal

from src.ui.styles import COLORS
from src.utils.i18n import tr
from src.ui.video_widget import VideoGrid


class CameraPage(QWidget):
    """Camera Page with video grid and controls."""
    
    toggle_system_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup camera page UI."""
        layout = QVBoxLayout(self)
        
        # Video Grid
        self.video_grid = VideoGrid()
        layout.addWidget(self.video_grid)
        
        # Bottom Controls
        controls = QHBoxLayout()
        
        self.btn_toggle = QPushButton(tr('start_system'))
        self.btn_toggle.setFixedWidth(150)
        self.btn_toggle.clicked.connect(self.toggle_system_clicked.emit)
        controls.addWidget(self.btn_toggle)
        
        # Grid Controls
        btn_1x1 = QPushButton("1x1")
        btn_1x1.setProperty("class", "secondary")
        btn_1x1.clicked.connect(lambda: self.video_grid.set_columns(1))
        
        btn_2x2 = QPushButton("2x2")
        btn_2x2.setProperty("class", "secondary")
        btn_2x2.clicked.connect(lambda: self.video_grid.set_columns(2))
        
        controls.addStretch()
        controls.addWidget(btn_1x1)
        controls.addWidget(btn_2x2)
        
        layout.addLayout(controls)
    
    def set_running_state(self, is_running: bool):
        """Update button state based on system running state."""
        self._is_running = is_running
        text = tr('card_stop_system') if is_running else tr('start_system')
        color_style = f"background-color: {COLORS['danger']};" if is_running else ""
        self.btn_toggle.setText(text)
        self.btn_toggle.setStyleSheet(color_style)
    
    def update_language(self):
        """Update text for live language change."""
        text = tr('card_stop_system') if self._is_running else tr('start_system')
        self.btn_toggle.setText(text)
