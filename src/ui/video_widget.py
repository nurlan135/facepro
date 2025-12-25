"""
FacePro Video Widget Module
Cyber-Brutalist Edition
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from enum import Enum

# Optional imports for OpenCV and NumPy
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None

if TYPE_CHECKING:
    import numpy as np

from PyQt6.QtWidgets import QLabel, QSizePolicy, QWidget, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QPen

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.helpers import cv2_to_qpixmap
from src.ui.styles import COLORS
from src.utils.i18n import tr


class CameraStatus(Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    OFFLINE = "offline"


class VideoWidget(QLabel):
    """
    Video stream widget with Cyber-Brutalist bracket borders.
    """
    
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    start_drawing = pyqtSignal() # New signal for specialized actions
    
    def __init__(self, camera_name: str = "Camera", parent=None):
        super().__init__(parent)
        
        self.camera_name = camera_name
        self._is_connected = False
        self._is_active = False 
        self._show_overlay = True
        self._fps = 0
        self._frame_count = 0
        
        # Camera status tracking
        self._camera_status = CameraStatus.OFFLINE
        
        # Widget setup
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Base cyber style
        self.setProperty("class", "video_widget")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_void']};
                border: 1px solid {COLORS['border_tech']};
            }}
        """)
        
        # Default placeholder
        self._show_placeholder()
        
        # FPS timer
        self._fps_timer = QTimer(self)
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(1000)
    
    def _show_placeholder(self):
        """Shows placeholder with tech look."""
        self.setText(f"{tr('cyber.system_offline')} // {self.camera_name}\n\n{tr('cyber.press_init')}")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: #050505;
                border: 1px dashed {COLORS['border_tech']};
                color: {COLORS['text_muted']};
                font-family: 'Consolas';
                font-size: 12px;
            }}
        """)
    
    def update_frame(self, frame: np.ndarray):
        if frame is None:
            return
        
        try:
            target_size = (self.width(), self.height())
            pixmap = cv2_to_qpixmap(frame, target_size)
            
            if not pixmap.isNull():
                self.setPixmap(pixmap)
                self._frame_count += 1
                self._is_connected = True
        except Exception as e:
            print(f"Frame error: {e}")
    
    def _update_fps(self):
        self._fps = self._frame_count
        self._frame_count = 0
    
    def set_connected(self, connected: bool):
        self._is_connected = connected
        if connected:
            self._camera_status = CameraStatus.CONNECTED
        else:
            self._show_placeholder()

    def set_camera_status(self, status: CameraStatus, attempt: int = 0, max_attempts: int = 5):
        self._camera_status = status
        
        if status == CameraStatus.CONNECTED:
            self._is_connected = True
        elif status == CameraStatus.CONNECTING:
            self._is_connected = False
            self.setText(f"{tr('cyber.linking')} // {self.camera_name}...")
        elif status == CameraStatus.FAILED:
            self._is_connected = False
            self.setText(f"{tr('cyber.link_failure')} // {self.camera_name}\n[{attempt}/{max_attempts}]")
            self.setStyleSheet(f"background: #1a0505; border: 1px solid {COLORS['alert_red']}; color: {COLORS['alert_red']};")
        elif status == CameraStatus.OFFLINE:
            self._is_connected = False
            self._show_placeholder()
    
    def get_widget(self, camera_name: str):
        return self if self.camera_name == camera_name else None

    # --- Cyber Paint Overlay ---
    def paintEvent(self, event):
        super().paintEvent(event)
        
        # Draw Tech Brackets (Corners)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        length = 20 # Length of corner bracket
        thickness = 2
        
        # Determine Color based on status/activity
        if self._is_active:
             color = QColor(COLORS['acid_green'])
        elif self._camera_status == CameraStatus.CONNECTED:
             try:
                 color = QColor(COLORS['cyber_cyan'])
                 color.setAlpha(150)
             except:
                 color = QColor(0, 240, 255, 150)
        else:
             color = QColor(COLORS['text_muted'])
             color.setAlpha(50)

        pen = QPen(color)
        pen.setWidth(thickness)
        painter.setPen(pen)
        
        # Top Left
        painter.drawLine(0, 0, length, 0)
        painter.drawLine(0, 0, 0, length)
        
        # Top Right
        painter.drawLine(w, 0, w-length, 0)
        painter.drawLine(w, 0, w, length)
        
        # Bottom Left
        painter.drawLine(0, h, length, h)
        painter.drawLine(0, h, 0, h-length)
        
        # Bottom Right
        painter.drawLine(w, h, w-length, h)
        painter.drawLine(w, h, w, h-length)
        
        # Draw Status Pill if connected
        if self._is_connected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.drawRect(5, 5, 100, 20)
            
            painter.setPen(QColor(COLORS['cyber_cyan']))
            painter.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            painter.drawText(10, 19, f"{self.camera_name} [LIVE]")
            
            # Record indicator (Dot)
            painter.setBrush(QColor(COLORS['alert_red']))
            if (self._frame_count % 30) < 15: # Blink (simulated by frame count not exact time but close enough)
                painter.drawEllipse(w-15, 10, 6, 6)

    # --- Mouse Events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            # Toggle active state visual
            self._is_active = not self._is_active
            self.update()
        super().mousePressEvent(event)
        
    def set_active(self, active: bool):
        self._is_active = active
        self.update()


class VideoGrid(QWidget):
    """
    Grid container for Cyber-VideoWidgets.
    """
    
    # Layout preset constants
    LAYOUT_1X1 = 1
    LAYOUT_2X2 = 2
    LAYOUT_3X3 = 3
    LAYOUT_4X4 = 4
    
    camera_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._widgets: dict[str, VideoWidget] = {}
        self._columns = 2
        self._setup_ui()
    
    def _setup_ui(self):
        from PyQt6.QtWidgets import QGridLayout
        self._layout = QGridLayout(self)
        self._layout.setSpacing(2) # Tiny gap for cyber look
        self._layout.setContentsMargins(0, 0, 0, 0) # Edge to edge
    
    def add_camera_view(self, camera_name: str) -> VideoWidget:
        if camera_name in self._widgets:
            return self._widgets[camera_name]
        
        widget = VideoWidget(camera_name)
        widget.clicked.connect(lambda: self.camera_selected.emit(camera_name))
        
        count = len(self._widgets)
        row = count // self._columns
        col = count % self._columns
        
        self._layout.addWidget(widget, row, col)
        self._widgets[camera_name] = widget
        
        return widget
    
    def clear_all(self):
        for name in list(self._widgets.keys()):
            widget = self._widgets.pop(name)
            self._layout.removeWidget(widget)
            widget.deleteLater()

    def get_widget(self, camera_name: str) -> Optional[VideoWidget]:
        return self._widgets.get(camera_name)

    def set_layout_preset(self, preset: int):
        self._columns = max(1, preset)
        self._reorganize_grid()

    def _reorganize_grid(self):
        for widget in self._widgets.values():
            self._layout.removeWidget(widget)
        
        for i, (name, widget) in enumerate(self._widgets.items()):
            row = i // self._columns
            col = i % self._columns
            self._layout.addWidget(widget, row, col)


class StatusIndicator(QWidget):
    """
    Status indicator widget (Restored for compatibility).
    """
    
    def __init__(self, size: int = 12, parent=None):
        super().__init__(parent)
        self._size = size
        self._color = QColor(COLORS['offline'])
        self.setFixedSize(size, size)
    
    def set_status(self, status: str):
        if status.lower() in ['online', 'connected', 'active']:
            self._color = QColor(COLORS['acid_green'])
        else:
            self._color = QColor(COLORS['alert_red'])
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, self._size - 2, self._size - 2)
