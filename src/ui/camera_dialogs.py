"""
FacePro Camera Dialogs Module
RTSP konfiqurasiya və lokal kamera seçim dialoquları.
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QGroupBox, QScrollArea, QWidget, QFrame, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import cv2
import re
import numpy as np

from src.ui.styles import COLORS, DARK_THEME
from src.ui.camera_preview import CameraPreviewThread, CameraCard
from src.utils.i18n import tr
from src.utils.helpers import build_rtsp_url
from src.utils.logger import get_logger

logger = get_logger()


class LocalCameraSelector(QDialog):
    """Lokal kamera seçim dialoqu."""
    
    MAX_CONCURRENT_PREVIEWS = 4
    MAX_CAMERAS_TO_SCAN = 10
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._preview_threads: List[CameraPreviewThread] = []
        self._camera_cards: List[CameraCard] = []
        self._selected_camera: Optional[Dict] = None
        self._setup_ui()
        
        # Scan-ı bir az gecikdir ki UI yüklənsin
        QTimer.singleShot(100, self._scan_cameras)
    
    def _setup_ui(self):
        """UI qurulumu."""
        self.setWindowTitle(tr('local_camera_title') if tr('local_camera_title') != 'local_camera_title' else "Lokal Kamera Seçimi")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("💻 " + (tr('local_camera_title') if tr('local_camera_title') != 'local_camera_title' else "Lokal Kamera Seçimi"))
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Loading indicator
        self.loading_label = QLabel(tr('scanning_cameras') if tr('scanning_cameras') != 'scanning_cameras' else "⏳ Kameralar axtarılır...")
        self.loading_label.setStyleSheet(f"font-size: 14px; color: {COLORS['text_muted']};")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)
        
        # Scroll area for camera cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setContentsMargins(10, 10, 10, 10)
        self.cards_layout.addStretch()
        
        self.scroll_area.setWidget(self.cards_container)
        self.scroll_area.hide()
        layout.addWidget(self.scroll_area)
        
        # No cameras message
        self.no_camera_label = QLabel()
        self.no_camera_label.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_muted']};
            padding: 20px;
        """)
        self.no_camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_camera_label.setWordWrap(True)
        self.no_camera_label.hide()
        layout.addWidget(self.no_camera_label)
        
        layout.addStretch()
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton(tr('back') if tr('back') != 'back' else "← Geri")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px 20px;
                color: {COLORS['text_muted']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_light']};
            }}
        """)
        back_btn.clicked.connect(self.reject)
        btn_layout.addWidget(back_btn)
        
        btn_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 " + (tr('refresh') if tr('refresh') != 'refresh' else "Yenilə"))
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px 20px;
                color: {COLORS['text_secondary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """)
        refresh_btn.clicked.connect(self._rescan_cameras)
        btn_layout.addWidget(refresh_btn)
        
        layout.addLayout(btn_layout)
    
    def _scan_cameras(self):
        """Bütün lokal kameraları aşkarlayır."""
        self.loading_label.show()
        self.scroll_area.hide()
        self.no_camera_label.hide()
        
        # Əvvəlki preview-ları dayandır
        self._stop_previews()
        
        # Kartları təmizlə
        for card in self._camera_cards:
            card.deleteLater()
        self._camera_cards.clear()
        
        # Layout-u təmizlə
        while self.cards_layout.count() > 1:  # Stretch saxla
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        found_cameras = []
        
        # Kameraları skan et
        for device_id in range(self.MAX_CAMERAS_TO_SCAN):
            cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
            if cap.isOpened():
                found_cameras.append(device_id)
                cap.release()
            
            # Maksimum preview limitinə çatdıqda dayandır
            if len(found_cameras) >= self.MAX_CONCURRENT_PREVIEWS:
                break
        
        self.loading_label.hide()
        
        if not found_cameras:
            self._show_no_cameras()
            return
        
        # Kamera kartları yarat
        self.scroll_area.show()
        
        for device_id in found_cameras:
            card = CameraCard(device_id, self)
            card.selected.connect(self._on_camera_selected)
            
            # Layout-a əlavə et (stretch-dən əvvəl)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            self._camera_cards.append(card)
            
            # Preview thread başlat
            thread = CameraPreviewThread(device_id, self)
            thread.frame_ready.connect(self._on_frame_ready)
            thread.info_ready.connect(self._on_info_ready)
            thread.error.connect(self._on_preview_error)
            thread.start()
            self._preview_threads.append(thread)
        
        logger.info(f"Found {len(found_cameras)} local cameras")
    
    def _rescan_cameras(self):
        """Kameraları yenidən skan edir."""
        self._scan_cameras()
    
    def _show_no_cameras(self):
        """Kamera tapılmadı mesajı göstərir."""
        self.no_camera_label.setText(
            "❌ " + (tr('no_cameras_found') if tr('no_cameras_found') != 'no_cameras_found' else "Kamera tapılmadı") + "\n\n" +
            "Mümkün səbəblər:\n"
            "• Kamera bağlı deyil\n"
            "• Kamera başqa proqram tərəfindən istifadə olunur\n"
            "• Driver problemi\n\n"
            "Həll yolları:\n"
            "• USB kameranı yenidən qoşun\n"
            "• Digər video proqramlarını bağlayın\n"
            "• Kompüteri yenidən başladın"
        )
        self.no_camera_label.show()
    
    def _on_frame_ready(self, device_id: int, frame):
        """Frame hazır olduqda."""
        for card in self._camera_cards:
            if card.get_device_id() == device_id:
                card.update_preview(frame)
                break
    
    def _on_info_ready(self, device_id: int, info: Dict):
        """Kamera info hazır olduqda."""
        for card in self._camera_cards:
            if card.get_device_id() == device_id:
                card.update_info(info)
                break
    
    def _on_preview_error(self, device_id: int, error: str):
        """Preview xətası olduqda."""
        for card in self._camera_cards:
            if card.get_device_id() == device_id:
                card.show_error(error)
                break
    
    def _on_camera_selected(self, device_id: int, info: Dict):
        """Kamera seçildikdə."""
        self._selected_camera = {
            'name': info.get('name', f"Camera {device_id}"),
            'source': str(device_id),
            'type': 'Webcam',
            'roi_points': []
        }
        self._stop_previews()
        self.accept()
    
    def _stop_previews(self):
        """Bütün preview thread-ləri dayandırır."""
        for thread in self._preview_threads:
            thread.stop()
        self._preview_threads.clear()
    
    def closeEvent(self, event):
        """Dialog bağlananda."""
        self._stop_previews()
        super().closeEvent(event)
    
    def get_camera_data(self) -> Optional[Dict]:
        """Seçilmiş kamera data-sını qaytarır."""
        return self._selected_camera


class RTSPConfigDialog(QDialog):
    """RTSP kamera konfiqurasiya dialoqu."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera_data: Optional[Dict] = None
        self._testing = False
        self._setup_ui()
    
    def _setup_ui(self):
        """UI qurulumu."""
        self.setWindowTitle(tr('rtsp_config_title') if tr('rtsp_config_title') != 'rtsp_config_title' else "RTSP Kamera Konfiqurasiyası")
        self.setMinimumWidth(500)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🌐 " + (tr('rtsp_config_title') if tr('rtsp_config_title') != 'rtsp_config_title' else "RTSP Kamera Konfiqurasiyası"))
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS['primary']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Form
        form_group = QGroupBox(tr('connection_settings') if tr('connection_settings') != 'connection_settings' else "Bağlantı Ayarları")
        form_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS['primary']};
            }}
        """)
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        
        # Camera name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("IP Camera 1")
        form_layout.addRow(tr('camera_name') if tr('camera_name') != 'camera_name' else "Kamera Adı:", self.name_edit)
        
        # IP Address
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("192.168.1.100")
        self.ip_edit.textChanged.connect(self._update_url_preview)
        form_layout.addRow(tr('ip_address') if tr('ip_address') != 'ip_address' else "IP Ünvanı:", self.ip_edit)
        
        # Port
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(554)
        self.port_spin.valueChanged.connect(self._update_url_preview)
        form_layout.addRow(tr('port') if tr('port') != 'port' else "Port:", self.port_spin)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("admin")
        self.username_edit.textChanged.connect(self._update_url_preview)
        form_layout.addRow(tr('username') if tr('username') != 'username' else "İstifadəçi:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.textChanged.connect(self._update_url_preview)
        form_layout.addRow(tr('password') if tr('password') != 'password' else "Şifrə:", self.password_edit)
        
        # Brand
        self.brand_combo = QComboBox()
        self.brand_combo.addItems(["Hikvision", "Dahua", "Generic"])
        self.brand_combo.currentIndexChanged.connect(self._update_url_preview)
        form_layout.addRow(tr('brand') if tr('brand') != 'brand' else "Marka:", self.brand_combo)
        
        # Channel
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        self.channel_spin.valueChanged.connect(self._update_url_preview)
        form_layout.addRow(tr('channel') if tr('channel') != 'channel' else "Kanal:", self.channel_spin)
        
        # Stream type
        self.stream_combo = QComboBox()
        self.stream_combo.addItems([
            tr('main_stream') if tr('main_stream') != 'main_stream' else "Əsas axın",
            tr('sub_stream') if tr('sub_stream') != 'sub_stream' else "Köməkçi axın"
        ])
        self.stream_combo.currentIndexChanged.connect(self._update_url_preview)
        form_layout.addRow(tr('stream_type') if tr('stream_type') != 'stream_type' else "Axın növü:", self.stream_combo)
        
        layout.addWidget(form_group)
        
        # URL Preview
        url_group = QGroupBox(tr('url_preview') if tr('url_preview') != 'url_preview' else "URL Önizləmə")
        url_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS['text_muted']};
            }}
        """)
        url_layout = QVBoxLayout(url_group)
        
        self.url_label = QLabel()
        self.url_label.setStyleSheet(f"""
            background-color: {COLORS['bg_dark']};
            padding: 10px;
            border-radius: 5px;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            color: {COLORS['success']};
        """)
        self.url_label.setWordWrap(True)
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        url_layout.addWidget(self.url_label)
        
        # Test button and preview
        test_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🔗 " + (tr('test_connection') if tr('test_connection') != 'test_connection' else "Bağlantını Test Et"))
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px 16px;
                color: {COLORS['text_secondary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: white;
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text_muted']};
            }}
        """)
        self.test_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_btn)
        
        self.test_status = QLabel()
        self.test_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        test_layout.addWidget(self.test_status)
        test_layout.addStretch()
        
        url_layout.addLayout(test_layout)
        
        # Preview frame
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(320, 180)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"""
            background-color: {COLORS['bg_dark']};
            border-radius: 5px;
            color: {COLORS['text_muted']};
        """)
        self.preview_label.setText("Test edildikdən sonra önizləmə görünəcək")
        self.preview_label.hide()
        url_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(url_group)
        
        # Validation error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        
        back_btn = QPushButton(tr('back') if tr('back') != 'back' else "← Geri")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px 20px;
                color: {COLORS['text_muted']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_light']};
            }}
        """)
        back_btn.clicked.connect(self.reject)
        btn_layout.addWidget(back_btn)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton(tr('save') if tr('save') != 'save' else "💾 Saxla")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # Initial URL update
        self._update_url_preview()
    
    def _update_url_preview(self):
        """URL preview-u yeniləyir."""
        ip = self.ip_edit.text() or "0.0.0.0"
        port = self.port_spin.value()
        username = self.username_edit.text() or "admin"
        password = self.password_edit.text()
        brand = self.brand_combo.currentText().lower()
        channel = self.channel_spin.value()
        stream = self.stream_combo.currentIndex()
        
        # Tam URL
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
        
        self.url_label.setText(masked_url)
        
        # Validation
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
        # Boş IP icazəlidir (placeholder)
        if not ip:
            return True
        
        # IPv4 pattern
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        
        # Hər oktetin 0-255 arasında olduğunu yoxla
        parts = ip.split('.')
        return all(0 <= int(p) <= 255 for p in parts)
    
    def _test_connection(self):
        """RTSP bağlantısını test edir."""
        if self._testing:
            return
        
        if not self._validate():
            return
        
        ip = self.ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Xəta", "IP ünvanı daxil edin")
            return
        
        self._testing = True
        self.test_btn.setEnabled(False)
        self.test_status.setText("⏳ Test edilir...")
        self.test_status.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px;")
        
        # URL yarat
        url = build_rtsp_url(
            ip=ip,
            username=self.username_edit.text() or "admin",
            password=self.password_edit.text(),
            port=self.port_spin.value(),
            channel=self.channel_spin.value(),
            stream=self.stream_combo.currentIndex(),
            brand=self.brand_combo.currentText().lower()
        )
        
        # Test connection (timeout 10 saniyə)
        try:
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
            
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    self.test_status.setText("✅ " + (tr('connection_success') if tr('connection_success') != 'connection_success' else "Bağlantı uğurlu!"))
                    self.test_status.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
                    
                    # Preview göstər
                    self._show_preview(frame)
                else:
                    self.test_status.setText("⚠️ Bağlandı, amma frame oxuna bilmədi")
                    self.test_status.setStyleSheet(f"color: {COLORS['warning']}; font-size: 12px;")
            else:
                self.test_status.setText("❌ " + (tr('connection_failed') if tr('connection_failed') != 'connection_failed' else "Bağlantı uğursuz"))
                self.test_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
                
        except Exception as e:
            self.test_status.setText(f"❌ Xəta: {str(e)[:50]}")
            self.test_status.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
            logger.error(f"RTSP test failed: {e}")
        
        self._testing = False
        self.test_btn.setEnabled(True)
    
    def _show_preview(self, frame):
        """Test frame-ini göstərir."""
        try:
            # Resize
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
        
        # URL yarat
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
