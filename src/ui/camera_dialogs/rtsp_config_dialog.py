"""
FacePro RTSP Config Dialog
RTSP/IP kamera konfiqurasiya dialoqu.
"""

from typing import Optional, Dict
import re
import threading

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QGroupBox, QScrollArea, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage

import cv2
import numpy as np

from src.ui.styles import COLORS, DARK_THEME
from src.utils.i18n import tr
from src.utils.helpers import build_rtsp_url
from src.utils.logger import get_logger

logger = get_logger()


class RTSPConfigDialog(QDialog):
    """RTSP kamera konfiqurasiya dialoqu - detallı."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera_data: Optional[Dict] = None
        self._testing = False
        self._test_result = None
        self._test_frame = None
        self._setup_ui()
    
    def _setup_ui(self):
        """UI qurulumu."""
        self.setWindowTitle(tr('rtsp_config_title'))
        self.setMinimumSize(700, 750)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Title
        title = QLabel(f"🌐 {tr('rtsp_config_title')}")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['primary']};")
        layout.addWidget(title)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # Connection Settings Form
        self._create_connection_form(scroll_layout)
        
        # URL Preview
        self._create_url_preview(scroll_layout)
        
        # Example Values
        self._create_examples_section(scroll_layout)
        
        # Connection Guide
        self._create_guide_section(scroll_layout)
        
        # Preview Area
        self._create_preview_area(scroll_layout)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Validation error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Bottom buttons
        self._create_buttons(layout)
        
        # Initial URL update
        self._update_url_preview()
    
    def _create_connection_form(self, parent_layout):
        """Connection settings form yaradır."""
        form_group = QGroupBox(tr('connection_settings'))
        form_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS['primary']};
            }}
        """)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 20, 15, 15)
        
        # Camera name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("IP Camera 1")
        form_layout.addRow(f"{tr('camera_name')}:", self.name_edit)
        
        # IP Address
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("192.168.1.100")
        self.ip_edit.textChanged.connect(self._update_url_preview)
        form_layout.addRow(f"{tr('ip_address')}:", self.ip_edit)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(554)
        self.port_spin.valueChanged.connect(self._update_url_preview)
        form_layout.addRow(f"{tr('port')}:", self.port_spin)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("admin")
        self.username_edit.textChanged.connect(self._update_url_preview)
        form_layout.addRow(f"{tr('username')}:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("12345")
        self.password_edit.textChanged.connect(self._update_url_preview)
        form_layout.addRow(f"{tr('password')}:", self.password_edit)
        
        # Brand
        self.brand_combo = QComboBox()
        self.brand_combo.addItems(["Hikvision", "Dahua", "TP-Link", "Generic"])
        self.brand_combo.currentIndexChanged.connect(self._update_url_preview)
        form_layout.addRow(f"{tr('brand')}:", self.brand_combo)
        
        # Channel
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        self.channel_spin.valueChanged.connect(self._update_url_preview)
        form_layout.addRow(f"{tr('channel')}:", self.channel_spin)
        
        # Stream type
        self.stream_combo = QComboBox()
        self.stream_combo.addItems([tr('main_stream'), tr('sub_stream')])
        self.stream_combo.currentIndexChanged.connect(self._update_url_preview)
        form_layout.addRow(f"{tr('stream_type')}:", self.stream_combo)
        
        parent_layout.addWidget(form_group)
    
    def _create_url_preview(self, parent_layout):
        """URL preview section yaradır."""
        url_group = QGroupBox(tr('url_preview'))
        url_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS['text_muted']};
            }}
        """)
        url_layout = QVBoxLayout(url_group)
        url_layout.setContentsMargins(15, 20, 15, 15)
        
        # Direct URL input hint
        url_hint = QLabel("Birbaşa URL yapışdırın və ya yuxarıdakı sahələri doldurun:")
        url_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        url_layout.addWidget(url_hint)
        
        # URL edit
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("rtsp://admin:password@192.168.1.100:554/stream")
        self.url_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                padding: 12px;
                border-radius: 5px;
                border: 1px solid {COLORS['border']};
                font-family: 'Consolas', monospace;
                font-size: 13px;
                color: {COLORS['success']};
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
        """)
        url_layout.addWidget(self.url_edit)
        
        # Test buttons row
        test_layout = QHBoxLayout()
        test_layout.setSpacing(10)
        
        self.test_btn = QPushButton(f"🔗 {tr('test_connection')}")
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_light']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.test_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_btn)
        
        # Test duration warning
        test_warning = QLabel(f"ℹ️ {tr('rtsp_test_duration')}")
        test_warning.setStyleSheet(f"""
            background-color: {COLORS['primary']};
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 12px;
        """)
        test_layout.addWidget(test_warning)
        test_layout.addStretch()
        url_layout.addLayout(test_layout)
        
        # Test status label
        self.test_status = QLabel("")
        self.test_status.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        url_layout.addWidget(self.test_status)
        
        parent_layout.addWidget(url_group)
    
    def _create_examples_section(self, parent_layout):
        """Example values section yaradır."""
        examples_group = QGroupBox(f"📍 {tr('rtsp_example_values')}")
        examples_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: {COLORS['bg_light']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS['danger']};
            }}
        """)
        examples_layout = QVBoxLayout(examples_group)
        examples_layout.setContentsMargins(15, 20, 15, 15)
        
        examples_text = QLabel(
            "• Hikvision: IP=192.168.1.100, Port=554, Endpoint=/Streaming/Channels/101\n"
            "• Dahua: IP=192.168.1.200, Port=554, Endpoint=/cam/realmonitor?channel=1&subtype=0\n"
            "• TP-Link: IP=192.168.1.50, Port=554, Endpoint=/stream1"
        )
        examples_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; line-height: 1.6;")
        examples_layout.addWidget(examples_text)
        
        parent_layout.addWidget(examples_group)
    
    def _create_guide_section(self, parent_layout):
        """Connection guide section yaradır."""
        guide_group = QGroupBox(f"📖 {tr('rtsp_connection_guide')}")
        guide_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: {COLORS['bg_light']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS['primary']};
            }}
        """)
        guide_layout = QVBoxLayout(guide_group)
        guide_layout.setContentsMargins(15, 20, 15, 15)
        
        quick_start = QLabel(
            f"<b>{tr('rtsp_quick_start')}:</b><br>"
            f"{tr('rtsp_quick_start_1')}<br>"
            f"{tr('rtsp_quick_start_2')}<br>"
            f"{tr('rtsp_quick_start_3')}<br>"
            f"{tr('rtsp_quick_start_4')}"
        )
        quick_start.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        quick_start.setWordWrap(True)
        guide_layout.addWidget(quick_start)
        
        important_notes = QLabel(
            f"<br><b>⚠️ {tr('rtsp_important_notes')}:</b><br>"
            f"• {tr('rtsp_note_network')}<br>"
            f"• {tr('rtsp_note_port')}<br>"
            f"• {tr('rtsp_note_path')}"
        )
        important_notes.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px;")
        important_notes.setWordWrap(True)
        guide_layout.addWidget(important_notes)
        
        parent_layout.addWidget(guide_group)
    
    def _create_preview_area(self, parent_layout):
        """Preview area yaradır."""
        # Status message
        self.status_label = QLabel(tr('rtsp_enter_url'))
        self.status_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 13px; padding: 10px;")
        self.status_label.setWordWrap(True)
        parent_layout.addWidget(self.status_label)
        
        # Preview group
        preview_group = QGroupBox()
        preview_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['bg_dark']};
            }}
        """)
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        
        self.preview_label = QLabel(tr('rtsp_preview_placeholder'))
        self.preview_label.setFixedSize(400, 225)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"""
            background-color: {COLORS['bg_medium']};
            border-radius: 8px;
            color: {COLORS['text_muted']};
            font-size: 14px;
        """)
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.preview_hint = QLabel(tr('rtsp_preview_hint'))
        self.preview_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        self.preview_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_hint)
        
        parent_layout.addWidget(preview_group)
    
    def _create_buttons(self, parent_layout):
        """Bottom buttons yaradır."""
        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton(f"← {tr('back')}")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 10px 25px;
                color: {COLORS['text_muted']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_light']};
            }}
        """)
        back_btn.clicked.connect(self.reject)
        btn_layout.addWidget(back_btn)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton(f"💾 {tr('save')}")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        parent_layout.addLayout(btn_layout)
    
    def _update_url_preview(self):
        """URL preview-u yeniləyir."""
        ip = self.ip_edit.text() or "0.0.0.0"
        port = self.port_spin.value()
        username = self.username_edit.text() or "admin"
        password = self.password_edit.text()
        brand = self.brand_combo.currentText().lower()
        channel = self.channel_spin.value()
        stream = self.stream_combo.currentIndex()
        
        url = build_rtsp_url(
            ip=ip,
            username=username,
            password=password,
            port=port,
            channel=channel,
            stream=stream,
            brand=brand
        )
        
        # Şifrəni mask et
        if password:
            masked_url = url.replace(f":{password}@", ":****@")
        else:
            masked_url = url
        
        self.url_edit.setText(masked_url)
        self._validate()
    
    def _validate(self) -> bool:
        """Form-u validasiya edir."""
        self.error_label.hide()
        
        ip = self.ip_edit.text().strip()
        
        if ip and not self._validate_ip(ip):
            self.error_label.setText("❌ " + (tr('invalid_ip') if tr('invalid_ip') != 'invalid_ip' else "Yanlış IP formatı"))
            self.error_label.show()
            return False
        
        return True
    
    def _validate_ip(self, ip: str) -> bool:
        """IP adresini validasiya edir."""
        if not ip:
            return True
        
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        parts = ip.split('.')
        return all(0 <= int(p) <= 255 for p in parts)
    
    def _test_connection(self):
        """RTSP bağlantısını test edir."""
        if self._testing:
            return
        
        url = self.url_edit.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Xəta", "RTSP URL daxil edin")
            return
        
        # If URL contains ****, replace with actual password
        if "****" in url:
            password = self.password_edit.text()
            url = url.replace(":****@", f":{password}@")
        
        self._testing = True
        self._test_url = url
        self.test_btn.setEnabled(False)
        self.test_status.setText("⏳ Test edilir... (10-30 saniyə)")
        self.test_status.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px;")
        
        # Run test in separate thread
        self._test_thread = threading.Thread(target=self._run_connection_test, daemon=True)
        self._test_thread.start()
        
        # Check result periodically
        self._test_timer = QTimer()
        self._test_timer.timeout.connect(self._check_test_result)
        self._test_timer.start(500)
    
    def _run_connection_test(self):
        """Background thread-də RTSP test."""
        self._test_result = None
        self._test_frame = None
        
        try:
            # RTSP üçün TCP
            import os
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            
            # FFMPEG backend-i məcbur et
            cap = cv2.VideoCapture(self._test_url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 15000)
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    self._test_result = "success"
                    self._test_frame = frame
                else:
                    self._test_result = "no_frame"
            else:
                self._test_result = "failed"
                
        except Exception as e:
            self._test_result = f"error:{str(e)[:50]}"
            logger.error(f"RTSP test failed: {e}")
    
    def _check_test_result(self):
        """Test nəticəsini yoxla."""
        if self._test_result is None:
            return
        
        self._test_timer.stop()
        self._testing = False
        self.test_btn.setEnabled(True)
        
        if self._test_result == "success":
            self.test_status.setText("✅ Bağlantı uğurlu!")
            self.test_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
            if self._test_frame is not None:
                self._show_preview(self._test_frame)
        elif self._test_result == "no_frame":
            self.test_status.setText("⚠️ Bağlandı, amma frame oxuna bilmədi")
            self.test_status.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px;")
        elif self._test_result == "failed":
            self.test_status.setText("❌ Bağlantı uğursuz")
            self.test_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        else:
            self.test_status.setText(f"❌ {self._test_result}")
            self.test_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
    
    def _show_preview(self, frame):
        """Test frame-ini göstərir."""
        try:
            preview = cv2.resize(frame, (320, 180))
            rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            
            q_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            self.preview_label.setPixmap(pixmap)
            self.preview_label.show()
        except Exception as e:
            logger.error(f"Preview error: {e}")
    
    def _save(self):
        """Kamera konfiqurasiyasını saxlayır."""
        if not self._validate():
            return
        
        name = self.name_edit.text().strip()
        ip = self.ip_edit.text().strip()
        
        if not name:
            name = f"IP Camera ({ip})" if ip else "IP Camera"
        
        if not ip:
            QMessageBox.warning(self, "Xəta", "IP ünvanı daxil edin")
            return
        
        url = build_rtsp_url(
            ip=ip,
            username=self.username_edit.text() or "admin",
            password=self.password_edit.text(),
            port=self.port_spin.value(),
            channel=self.channel_spin.value(),
            stream=self.stream_combo.currentIndex(),
            brand=self.brand_combo.currentText().lower()
        )
        
        self._camera_data = {
            'name': name,
            'source': url,
            'type': 'RTSP (IP Camera)',
            'roi_points': [],
            'rtsp_config': {
                'ip': ip,
                'port': self.port_spin.value(),
                'username': self.username_edit.text(),
                'password': self.password_edit.text(),
                'brand': self.brand_combo.currentText(),
                'channel': self.channel_spin.value(),
                'stream': self.stream_combo.currentIndex()
            }
        }
        
        self.accept()
    
    def get_camera_data(self) -> Optional[Dict]:
        """Kamera data-sını qaytarır."""
        return self._camera_data
