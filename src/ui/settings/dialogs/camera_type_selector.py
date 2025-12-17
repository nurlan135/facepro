"""
FacePro Camera Type Selector Dialog
Kamera növü seçim dialoqu.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt

from src.ui.styles import DARK_THEME, COLORS
from src.utils.i18n import tr


class CameraTypeSelector(QDialog):
    """Kamera növü seçim dialoqu."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_type = None
        self._setup_ui()
    
    def _setup_ui(self):
        title_text = tr('select_camera_type') if tr('select_camera_type') != 'select_camera_type' else "Kamera Seçin"
        self.setWindowTitle(title_text)
        self.setFixedSize(500, 350)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel(f"🎥 {title_text}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle_text = tr('select_camera_type_desc') if tr('select_camera_type_desc') != 'select_camera_type_desc' else "Kamera növünü seçin"
        subtitle = QLabel(subtitle_text)
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Buttons container
        btn_container = QHBoxLayout()
        btn_container.setSpacing(20)
        
        # RTSP/IP Camera button
        rtsp_btn = self._create_camera_button(
            icon="🌐",
            title="RTSP / IP Kamera",
            desc="Hikvision, Dahua, TP-Link",
            color=COLORS['primary'],
            bg_color=COLORS['bg_light'],
            hover_color=COLORS['bg_medium']
        )
        rtsp_btn.clicked.connect(lambda: self._select_type("rtsp"))
        btn_container.addWidget(rtsp_btn)
        
        # Webcam button
        webcam_btn = self._create_camera_button(
            icon="💻",
            title="Lokal Kamera",
            desc="USB webcam, laptop kamerası",
            color=COLORS['success'],
            bg_color=COLORS['surface'],
            hover_color=COLORS['surface_light']
        )
        webcam_btn.clicked.connect(lambda: self._select_type("webcam"))
        btn_container.addWidget(webcam_btn)
        
        layout.addLayout(btn_container)
        layout.addSpacing(10)
        
        # Cancel button
        cancel_text = tr('cancel') if tr('cancel') != 'cancel' else "Ləğv et"
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setFixedWidth(120)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px 16px;
                color: {COLORS['text_muted']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        
        cancel_container = QHBoxLayout()
        cancel_container.addStretch()
        cancel_container.addWidget(cancel_btn)
        cancel_container.addStretch()
        layout.addLayout(cancel_container)
    
    def _create_camera_button(self, icon: str, title: str, desc: str, 
                               color: str, bg_color: str, hover_color: str) -> QPushButton:
        """Kamera seçim düyməsi yaradır."""
        btn = QPushButton()
        btn.setFixedSize(200, 150)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
                padding: 15px;
            }}
            QPushButton:hover {{
                border-color: {color};
                background-color: {hover_color};
            }}
        """)
        
        btn_layout = QVBoxLayout(btn)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 40px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(title_label)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"font-size: 10px; color: {COLORS['text_muted']};")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(desc_label)
        
        return btn
    
    def _select_type(self, camera_type: str):
        self.selected_type = camera_type
        self.accept()
