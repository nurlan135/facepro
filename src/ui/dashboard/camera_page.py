"""
FacePro Dashboard Camera Page
Video grid and camera controls with mode selection.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from src.ui.styles import COLORS
from src.utils.i18n import tr
from src.ui.video_widget import VideoGrid


class CameraPage(QWidget):
    """Camera Page with video grid and controls."""
    
    select_camera_clicked = pyqtSignal()  # Kamera seçim dialoqu
    start_clicked = pyqtSignal()  # Sistemi başlat
    stop_clicked = pyqtSignal()  # Sistemi dayandır
    toggle_system_clicked = pyqtSignal()  # Legacy - köhnə uyğunluq üçün
    mode_changed = pyqtSignal(str)  # 'security', 'baby', 'object'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._current_mode = 'security'
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup camera page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Camera Control Panel with Mode Selection
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # Video Grid
        self.video_grid = VideoGrid()
        layout.addWidget(self.video_grid)
    
    def _create_control_panel(self) -> QFrame:
        """Kamera kontrol paneli yaradır."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(12)
        
        # Title
        title = QLabel(f"📹 {tr('camera_control')}")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['primary']};
            background: transparent;
        """)
        panel_layout.addWidget(title)
        
        # Mode Selection Group
        mode_group = QGroupBox(f"🎯 {tr('working_mode')}")
        mode_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS['primary']};
            }}
        """)
        
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setSpacing(20)
        
        # Radio button style
        radio_style = f"""
            QRadioButton {{
                color: {COLORS['text_secondary']};
                font-size: 13px;
                spacing: 8px;
                background: transparent;
            }}
            QRadioButton:checked {{
                color: {COLORS['text_primary']};
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 2px solid {COLORS['border']};
                border-radius: 9px;
                background: transparent;
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {COLORS['primary']};
                border-radius: 9px;
                background: {COLORS['primary']};
            }}
        """
        
        self.mode_group = QButtonGroup(self)
        
        # Security Mode (Face Recognition)
        self.radio_security = QRadioButton(f"🔒 {tr('mode_security')}")
        self.radio_security.setStyleSheet(radio_style)
        self.radio_security.setChecked(True)
        self.mode_group.addButton(self.radio_security, 0)
        mode_layout.addWidget(self.radio_security)
        
        # Baby Monitoring Mode
        self.radio_baby = QRadioButton(f"👶 {tr('mode_baby')}")
        self.radio_baby.setStyleSheet(radio_style)
        self.mode_group.addButton(self.radio_baby, 1)
        mode_layout.addWidget(self.radio_baby)
        
        # Object Detection Mode
        self.radio_object = QRadioButton(f"📦 {tr('mode_object')}")
        self.radio_object.setStyleSheet(radio_style)
        self.mode_group.addButton(self.radio_object, 2)
        mode_layout.addWidget(self.radio_object)
        
        mode_layout.addStretch()
        
        # Connect mode change
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        
        panel_layout.addWidget(mode_group)
        
        # Action Buttons Row
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        # Select Camera Button (Blue)
        self.btn_select_camera = QPushButton(f"📷 {tr('btn_select_camera')}")
        self.btn_select_camera.setFixedHeight(36)
        self.btn_select_camera.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary']};
            }}
        """)
        self.btn_select_camera.clicked.connect(self._on_select_camera)
        action_layout.addWidget(self.btn_select_camera)
        
        # Start Button (Green)
        self.btn_start = QPushButton(f"▶ {tr('btn_start')}")
        self.btn_start.setFixedHeight(36)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
            QPushButton:pressed {{
                background-color: {COLORS['success']};
            }}
        """)
        self.btn_start.clicked.connect(self._on_start)
        action_layout.addWidget(self.btn_start)
        
        # Stop Button (Red)
        self.btn_stop = QPushButton(f"⏹ {tr('btn_stop')}")
        self.btn_stop.setFixedHeight(36)
        self.btn_stop.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
            QPushButton:pressed {{
                background-color: {COLORS['danger']};
            }}
        """)
        self.btn_stop.clicked.connect(self._on_stop)
        action_layout.addWidget(self.btn_stop)
        
        action_layout.addStretch()
        
        # Grid Controls
        grid_btn_style = f"""
            QPushButton {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface_light']};
                border-color: {COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """
        
        btn_1x1 = QPushButton("1×1")
        btn_1x1.setToolTip("1 Kamera (Tam Ekran)")
        btn_1x1.setFixedSize(40, 36)
        btn_1x1.setStyleSheet(grid_btn_style)
        btn_1x1.clicked.connect(lambda: self.video_grid.set_layout_preset(1))
        
        btn_2x2 = QPushButton("2×2")
        btn_2x2.setToolTip("4 Kamera Grid")
        btn_2x2.setFixedSize(40, 36)
        btn_2x2.setStyleSheet(grid_btn_style)
        btn_2x2.clicked.connect(lambda: self.video_grid.set_layout_preset(2))
        
        btn_3x3 = QPushButton("3×3")
        btn_3x3.setToolTip("9 Kamera Grid")
        btn_3x3.setFixedSize(40, 36)
        btn_3x3.setStyleSheet(grid_btn_style)
        btn_3x3.clicked.connect(lambda: self.video_grid.set_layout_preset(3))
        
        btn_4x4 = QPushButton("4×4")
        btn_4x4.setToolTip("16 Kamera Grid")
        btn_4x4.setFixedSize(40, 36)
        btn_4x4.setStyleSheet(grid_btn_style)
        btn_4x4.clicked.connect(lambda: self.video_grid.set_layout_preset(4))
        
        action_layout.addWidget(btn_1x1)
        action_layout.addWidget(btn_2x2)
        action_layout.addWidget(btn_3x3)
        action_layout.addWidget(btn_4x4)
        
        panel_layout.addLayout(action_layout)
        
        # Status Label
        self.status_label = QLabel(f"📍 {tr('status_no_camera')}")
        self.status_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            padding: 5px 0;
            background: transparent;
        """)
        panel_layout.addWidget(self.status_label)
        
        return panel
    
    def _on_mode_changed(self, button):
        """Mod dəyişdikdə."""
        mode_map = {
            0: 'security',
            1: 'baby', 
            2: 'object'
        }
        mode_id = self.mode_group.id(button)
        self._current_mode = mode_map.get(mode_id, 'security')
        self.mode_changed.emit(self._current_mode)
    
    def _on_select_camera(self):
        """Kamera seçimi dialoqu."""
        self.select_camera_clicked.emit()
    
    def _on_start(self):
        """Sistemi başlat."""
        if not self._is_running:
            self.start_clicked.emit()
    
    def _on_stop(self):
        """Sistemi dayandır."""
        if self._is_running:
            self.stop_clicked.emit()
    
    def set_camera_status(self, camera_url: str):
        """Kamera statusunu yenilə."""
        if camera_url:
            self.status_label.setText(f"📍 {tr('status_camera_selected')}: {camera_url}")
        else:
            self.status_label.setText(f"📍 {tr('status_no_camera')}")
    
    def get_current_mode(self) -> str:
        """Cari modu qaytarır."""
        return self._current_mode
    
    def set_running_state(self, is_running: bool):
        """Update button state based on system running state."""
        self._is_running = is_running
        # Update button states
        self.btn_start.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)
        
        # Visual feedback
        if is_running:
            self.btn_start.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['border']};
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 13px;
                }}
            """)
        else:
            self.btn_start.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['success']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: #27ae60;
                }}
            """)
    
    def update_language(self):
        """Update text for live language change."""
        self.btn_select_camera.setText(f"📷 {tr('btn_select_camera')}")
        self.btn_start.setText(f"▶ {tr('btn_start')}")
        self.btn_stop.setText(f"⏹ {tr('btn_stop')}")
