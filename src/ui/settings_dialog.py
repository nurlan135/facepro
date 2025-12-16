"""
FacePro Settings Dialog Module
Tətbiq ayarları üçün dialog pəncərəsi.
"""

from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import load_config, save_config, load_cameras, save_cameras, build_rtsp_url
from src.ui.styles import DARK_THEME, COLORS
from src.hardware.gsm_modem import GSMModem
from src.hardware.telegram_notifier import TelegramNotifier
from src.hardware.telegram_notifier import TelegramNotifier
from src.utils.i18n import tr, set_language
from src.ui.zone_editor import ZoneEditorDialog

logger = get_logger()


class CameraDialog(QDialog):
    """Kamera əlavə etmə/redaktə dialoqu."""
    
    def __init__(self, camera_data: Optional[Dict] = None, parent=None):
        """
        Args:
            camera_data: Redaktə üçün mövcud kamera data-sı (None = yeni)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._camera_data = camera_data or {}
        self._is_edit_mode = camera_data is not None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle("Add Camera" if not self._is_edit_mode else "Edit Camera")
        self.setMinimumWidth(450)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        
        # Form
        form = QFormLayout()
        form.setSpacing(15)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Camera 1")
        form.addRow("Name:", self.name_edit)
        
        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["RTSP (IP Camera)", "Webcam", "Video File"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Type:", self.type_combo)
        
        # RTSP Settings Group
        self.rtsp_group = QGroupBox("RTSP Settings")
        rtsp_layout = QFormLayout(self.rtsp_group)
        
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("192.168.1.100")
        rtsp_layout.addRow("IP Address:", self.ip_edit)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(554)
        rtsp_layout.addRow("Port:", self.port_spin)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("admin")
        rtsp_layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        rtsp_layout.addRow("Password:", self.password_edit)
        
        self.brand_combo = QComboBox()
        self.brand_combo.addItems(["Hikvision", "Dahua", "Generic"])
        rtsp_layout.addRow("Brand:", self.brand_combo)
        
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 16)
        self.channel_spin.setValue(1)
        rtsp_layout.addRow("Channel:", self.channel_spin)
        
        self.stream_combo = QComboBox()
        self.stream_combo.addItems(["Main Stream", "Sub Stream"])
        rtsp_layout.addRow("Stream:", self.stream_combo)
        
        layout.addLayout(form)
        layout.addWidget(self.rtsp_group)
        
        # Webcam Settings
        self.webcam_group = QGroupBox("Webcam Settings")
        webcam_layout = QFormLayout(self.webcam_group)
        
        self.webcam_id_spin = QSpinBox()
        self.webcam_id_spin.setRange(0, 10)
        webcam_layout.addRow("Device ID:", self.webcam_id_spin)
        
        layout.addWidget(self.webcam_group)
        self.webcam_group.hide()
        
        # File Settings
        self.file_group = QGroupBox("Video File")
        file_layout = QHBoxLayout(self.file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addWidget(self.file_group)
        self.file_group.hide()
        
        # Generated URL (readonly)
        self.url_edit = QLineEdit()
        self.url_edit.setReadOnly(True)
        self.url_edit.setStyleSheet(f"background-color: {COLORS['bg_light']};")
        form.addRow("Source URL:", self.url_edit)
        
        # Update URL on changes
        self.ip_edit.textChanged.connect(self._update_url)
        self.port_spin.valueChanged.connect(self._update_url)
        self.username_edit.textChanged.connect(self._update_url)
        self.password_edit.textChanged.connect(self._update_url)
        self.brand_combo.currentIndexChanged.connect(self._update_url)
        self.channel_spin.valueChanged.connect(self._update_url)
        self.brand_combo.currentIndexChanged.connect(self._update_url)
        self.channel_spin.valueChanged.connect(self._update_url)
        self.stream_combo.currentIndexChanged.connect(self._update_url)
        
        # Zone Settings
        zone_btn = QPushButton("Set Detection Zone (ROI)")
        zone_btn.clicked.connect(self._set_zone)
        form.addRow("Zone:", zone_btn)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_type_changed(self, index: int):
        """Kamera tipi dəyişdikdə."""
        self.rtsp_group.setVisible(index == 0)
        self.webcam_group.setVisible(index == 1)
        self.file_group.setVisible(index == 2)
        self._update_url()
    
    def _update_url(self):
        """Source URL-i yeniləyir."""
        if self.type_combo.currentIndex() == 0:  # RTSP
            url = build_rtsp_url(
                ip=self.ip_edit.text() or "0.0.0.0",
                username=self.username_edit.text() or "admin",
                password=self.password_edit.text(),
                port=self.port_spin.value(),
                channel=self.channel_spin.value(),
                stream=self.stream_combo.currentIndex(),
                brand=self.brand_combo.currentText().lower()
            )
        elif self.type_combo.currentIndex() == 1:  # Webcam
            url = str(self.webcam_id_spin.value())
        else:  # File
            url = self.file_path_edit.text()
        
        self.url_edit.setText(url)
    
    def _browse_file(self):
        """Video faylı seçmək."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )
        if path:
            self.file_path_edit.setText(path)
            self._update_url()
    
    def _load_data(self):
        """Mövcud data-nı yükləyir."""
        if not self._camera_data:
            return
        
        self.name_edit.setText(self._camera_data.get('name', ''))
        
        source = self._camera_data.get('source', '')
        if source.startswith('rtsp'):
            self.type_combo.setCurrentIndex(0)
            # Parse RTSP URL (simplified)
            self.url_edit.setText(source)
        elif source.isdigit():
            self.type_combo.setCurrentIndex(1)
            self.webcam_id_spin.setValue(int(source))
        else:
            self.type_combo.setCurrentIndex(2)
            self.file_path_edit.setText(source)
    
    def _save(self):
        """Kamera data-sını saxlayır."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a camera name.")
            return
        
        source = self.url_edit.text()
        if not source:
            QMessageBox.warning(self, "Error", "Please configure camera source.")
            return
        
        self._camera_data = {
            'name': name,
            'source': source,
            'type': self.type_combo.currentText(),
            'roi_points': self._camera_data.get('roi_points', [])
        }
        
        self.accept()
    
    def get_camera_data(self) -> Dict:
        """Kamera data-sını qaytarır."""
        return self._camera_data
        
    def _set_zone(self):
        """Zone editor-u açır."""
        # Cari URL-i yenilə (redaktə olunmuş ola bilər)
        self._update_url()
        temp_data = self._camera_data.copy()
        temp_data['source'] = self.url_edit.text()
        
        dialog = ZoneEditorDialog(temp_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._camera_data['roi_points'] = dialog.get_roi_points()
            QMessageBox.information(self, "Success", "Zone updated.")


class SettingsDialog(QDialog):
    """Əsas ayarlar dialoqu."""
    
    settings_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        """
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._config = load_config()
        self._cameras = load_cameras()
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle(tr('settings_title'))
        self.setMinimumSize(600, 500)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        
        # Tab Widget
        tabs = QTabWidget()
        
        # General Tab
        tabs.addTab(self._create_general_tab(), tr('tab_general'))
        
        # Cameras Tab
        tabs.addTab(self._create_cameras_tab(), tr('tab_camera'))
        
        # AI Tab
        tabs.addTab(self._create_ai_tab(), tr('tab_ai'))
        
        # Notifications Tab
        tabs.addTab(self._create_notifications_tab(), tr('tab_notifications'))
        
        # Storage Tab
        tabs.addTab(self._create_storage_tab(), tr('tab_storage'))
        
        layout.addWidget(tabs)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(tr('btn_cancel'))
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)
        
        save_btn = QPushButton(tr('btn_save'))
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_general_tab(self) -> QWidget:
        """General tab yaradır."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # App Settings
        app_group = QGroupBox("Application")
        app_layout = QFormLayout(app_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Azərbaycanca", "English", "Русский"])
        app_layout.addRow(f"{tr('lbl_language')}:", self.language_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        app_layout.addRow(f"{tr('lbl_theme')}:", self.theme_combo)
        
        self.autostart_check = QCheckBox("Start with Windows")
        app_layout.addRow("", self.autostart_check)
        
        self.minimize_tray_check = QCheckBox("Minimize to system tray")
        app_layout.addRow("", self.minimize_tray_check)
        
        layout.addWidget(app_group)
        layout.addStretch()
        
        return widget
    
    def _create_cameras_tab(self) -> QWidget:
        """Cameras tab yaradır."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Camera list
        self.camera_list = QListWidget()
        layout.addWidget(self.camera_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Camera")
        add_btn.clicked.connect(self._add_camera)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self._edit_camera)
        btn_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.setProperty("class", "danger")
        remove_btn.clicked.connect(self._remove_camera)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_ai_tab(self) -> QWidget:
        """AI settings tab yaradır."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Motion Detection
        motion_group = QGroupBox("Motion Detection")
        motion_layout = QFormLayout(motion_group)
        
        self.motion_threshold_spin = QSpinBox()
        self.motion_threshold_spin.setRange(1, 100)
        self.motion_threshold_spin.setValue(25)
        motion_layout.addRow("Threshold:", self.motion_threshold_spin)
        
        layout.addWidget(motion_group)
        
        # Face Recognition
        face_group = QGroupBox("Face Recognition")
        face_layout = QFormLayout(face_group)
        
        self.face_confidence_spin = QDoubleSpinBox()
        self.face_confidence_spin.setRange(0.1, 1.0)
        self.face_confidence_spin.setSingleStep(0.05)
        self.face_confidence_spin.setValue(0.6)
        face_layout.addRow("Confidence:", self.face_confidence_spin)
        
        layout.addWidget(face_group)
        
        # Re-ID
        reid_group = QGroupBox("Person Re-ID")
        reid_layout = QFormLayout(reid_group)
        
        self.reid_confidence_spin = QDoubleSpinBox()
        self.reid_confidence_spin.setRange(0.1, 1.0)
        self.reid_confidence_spin.setSingleStep(0.05)
        self.reid_confidence_spin.setValue(0.75)
        reid_layout.addRow("Confidence:", self.reid_confidence_spin)
        
        layout.addWidget(reid_group)
        
        # Gait Recognition
        gait_group = QGroupBox(tr('gait_recognition'))
        gait_layout = QFormLayout(gait_group)
        
        self.gait_enabled_check = QCheckBox(tr('gait_enabled'))
        self.gait_enabled_check.setToolTip(tr('gait_settings'))
        gait_layout.addRow("", self.gait_enabled_check)
        
        self.gait_threshold_spin = QDoubleSpinBox()
        self.gait_threshold_spin.setRange(0.50, 0.95)
        self.gait_threshold_spin.setSingleStep(0.05)
        self.gait_threshold_spin.setValue(0.70)
        self.gait_threshold_spin.setToolTip(tr('gait_threshold_desc'))
        gait_layout.addRow(f"{tr('gait_threshold')}:", self.gait_threshold_spin)
        
        self.gait_sequence_spin = QSpinBox()
        self.gait_sequence_spin.setRange(20, 60)
        self.gait_sequence_spin.setValue(30)
        self.gait_sequence_spin.setSuffix(" frames")
        self.gait_sequence_spin.setToolTip(tr('gait_sequence_desc'))
        gait_layout.addRow(f"{tr('gait_sequence_length')}:", self.gait_sequence_spin)
        
        layout.addWidget(gait_group)
        layout.addStretch()
        
        return widget
    
    def _create_notifications_tab(self) -> QWidget:
        """Notifications tab yaradır."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Telegram
        telegram_group = QGroupBox("Telegram Bot")
        telegram_layout = QFormLayout(telegram_group)
        
        self.telegram_token_edit = QLineEdit()
        self.telegram_token_edit.setPlaceholderText("Bot token from @BotFather")
        self.telegram_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        telegram_layout.addRow("Bot Token:", self.telegram_token_edit)
        
        self.telegram_chat_edit = QLineEdit()
        self.telegram_chat_edit.setPlaceholderText("Chat ID")
        telegram_layout.addRow("Chat ID:", self.telegram_chat_edit)
        
        test_telegram_btn = QPushButton("Test Connection")
        test_telegram_btn.setProperty("class", "secondary")
        test_telegram_btn.clicked.connect(self._test_telegram)
        telegram_layout.addRow("", test_telegram_btn)
        
        # Telegram Notification Settings
        notif_group = QGroupBox("Bildiriş Ayarları")
        notif_layout = QFormLayout(notif_group)
        
        self.telegram_enabled_check = QCheckBox("Telegram bildirişlərini aktiv et")
        notif_layout.addRow("", self.telegram_enabled_check)
        
        self.notify_known_check = QCheckBox("Tanınmış şəxslər üçün də bildiriş göndər")
        self.notify_known_check.setToolTip("Söndürülübsə, yalnız naməlum şəxslər üçün bildiriş gəlir")
        notif_layout.addRow("", self.notify_known_check)
        
        self.notification_interval_spin = QSpinBox()
        self.notification_interval_spin.setRange(5, 300)
        self.notification_interval_spin.setSuffix(" saniyə")
        self.notification_interval_spin.setValue(30)
        self.notification_interval_spin.setToolTip("Eyni şəxs üçün bildiriş arası minimum fasilə")
        notif_layout.addRow("Bildiriş intervalı:", self.notification_interval_spin)
        
        layout.addWidget(telegram_group)
        layout.addWidget(notif_group)
        
        # GSM
        gsm_group = QGroupBox("GSM Modem (Offline SMS)")
        gsm_layout = QFormLayout(gsm_group)
        
        self.gsm_enabled_check = QCheckBox("Enable GSM Fallback")
        gsm_layout.addRow("", self.gsm_enabled_check)
        
        self.gsm_port_combo = QComboBox()
        self.gsm_port_combo.addItems(["COM1", "COM2", "COM3", "COM4"])
        
        # Mövcud portları yüklə
        refresh_ports_btn = QPushButton("Refresh")
        refresh_ports_btn.setFixedWidth(80)
        refresh_ports_btn.clicked.connect(self._refresh_com_ports)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(self.gsm_port_combo)
        port_layout.addWidget(refresh_ports_btn)
        gsm_layout.addRow("COM Port:", port_layout)
        
        self.gsm_phone_edit = QLineEdit()
        self.gsm_phone_edit.setPlaceholderText("+994501234567")
        gsm_layout.addRow("Phone Number:", self.gsm_phone_edit)
        
        test_gsm_btn = QPushButton("Test SMS")
        test_gsm_btn.setProperty("class", "secondary")
        gsm_layout.addRow("", test_gsm_btn)
        
        layout.addWidget(gsm_group)
        layout.addStretch()
        
        return widget
    
    def _create_storage_tab(self) -> QWidget:
        """Storage tab yaradır."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Storage Settings
        storage_group = QGroupBox("Storage Settings")
        storage_layout = QFormLayout(storage_group)
        
        self.max_storage_spin = QSpinBox()
        self.max_storage_spin.setRange(1, 1000)
        self.max_storage_spin.setSuffix(" GB")
        self.max_storage_spin.setValue(10)
        storage_layout.addRow("Max Storage:", self.max_storage_spin)
        
        self.cleanup_interval_spin = QSpinBox()
        self.cleanup_interval_spin.setRange(1, 60)
        self.cleanup_interval_spin.setSuffix(" min")
        self.cleanup_interval_spin.setValue(10)
        storage_layout.addRow("Cleanup Interval:", self.cleanup_interval_spin)
        
        layout.addWidget(storage_group)
        layout.addStretch()
        
        return widget
    
    def _load_settings(self):
        """Ayarları yükləyir."""
        # UI settings
        ui_config = self._config.get('ui', {})
        theme = ui_config.get('theme', 'dark')
        self.theme_combo.setCurrentText(theme.capitalize())
        
        lang_code = ui_config.get('language', 'en')
        lang_map = {'az': 'Azərbaycanca', 'en': 'English', 'ru': 'Русский'}
        self.language_combo.setCurrentText(lang_map.get(lang_code, 'English'))
        
        # AI settings
        ai_config = self._config.get('ai', {})
        self.motion_threshold_spin.setValue(ai_config.get('motion_threshold', 25))
        self.face_confidence_spin.setValue(ai_config.get('face_confidence_threshold', 0.6))
        self.reid_confidence_spin.setValue(ai_config.get('reid_confidence_threshold', 0.75))
        
        # Gait settings
        gait_config = self._config.get('gait', {})
        self.gait_enabled_check.setChecked(gait_config.get('enabled', True))
        self.gait_threshold_spin.setValue(gait_config.get('threshold', 0.70))
        self.gait_sequence_spin.setValue(gait_config.get('sequence_length', 30))
        
        # Telegram
        telegram_config = self._config.get('telegram', {})
        self.telegram_token_edit.setText(telegram_config.get('bot_token', ''))
        self.telegram_chat_edit.setText(telegram_config.get('chat_id', ''))
        self.telegram_enabled_check.setChecked(telegram_config.get('enabled', True))
        self.notify_known_check.setChecked(telegram_config.get('notify_known_persons', False))
        self.notification_interval_spin.setValue(telegram_config.get('notification_interval', 30))
        
        # GSM
        gsm_config = self._config.get('gsm', {})
        self.gsm_enabled_check.setChecked(gsm_config.get('enabled', False))
        self.gsm_phone_edit.setText(gsm_config.get('phone_number', ''))
        
        # Storage
        storage_config = self._config.get('storage', {})
        self.max_storage_spin.setValue(int(storage_config.get('max_size_gb', 10)))
        self.cleanup_interval_spin.setValue(storage_config.get('fifo_check_interval_minutes', 10))
        
        # Cameras
        self._refresh_camera_list()
        
        # COM ports
        self._refresh_com_ports()
    
    def _refresh_camera_list(self):
        """Kamera siyahısını yeniləyir."""
        self.camera_list.clear()
        for camera in self._cameras:
            item = QListWidgetItem(f"{camera['name']} ({camera.get('type', 'Unknown')})")
            item.setData(Qt.ItemDataRole.UserRole, camera)
            self.camera_list.addItem(item)
    
    def _refresh_com_ports(self):
        """COM portlarını yeniləyir."""
        ports = GSMModem.list_available_ports()
        self.gsm_port_combo.clear()
        for port in ports:
            self.gsm_port_combo.addItem(f"{port['port']} - {port['description']}", port['port'])
    
    def _test_telegram(self):
        """Telegram bağlantısını test edir."""
        token = self.telegram_token_edit.text().strip()
        chat_id = self.telegram_chat_edit.text().strip()
        
        if not token or not chat_id:
            QMessageBox.warning(
                self, "Error",
                "Please enter both Bot Token and Chat ID."
            )
            return
        
        # Test notifier yaratmaq
        notifier = TelegramNotifier(bot_token=token, chat_id=chat_id)
        success, message = notifier.test_connection()
        notifier.stop()
        
        if success:
            QMessageBox.information(
                self, "Success",
                f"✅ {message}\n\nTest mesajı Telegram-a göndərildi!"
            )
        else:
            QMessageBox.critical(
                self, "Error",
                f"❌ {message}"
            )
    
    def _add_camera(self):
        """Yeni kamera əlavə edir."""
        dialog = CameraDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            camera_data = dialog.get_camera_data()
            self._cameras.append(camera_data)
            self._refresh_camera_list()
    
    def _edit_camera(self):
        """Seçilmiş kameranı redaktə edir."""
        item = self.camera_list.currentItem()
        if not item:
            return
        
        camera_data = item.data(Qt.ItemDataRole.UserRole)
        dialog = CameraDialog(camera_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            idx = self.camera_list.currentRow()
            self._cameras[idx] = dialog.get_camera_data()
            self._refresh_camera_list()
    
    def _remove_camera(self):
        """Seçilmiş kameranı silir."""
        item = self.camera_list.currentItem()
        if not item:
            return
        
        reply = QMessageBox.question(
            self, "Confirm", "Are you sure you want to remove this camera?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            idx = self.camera_list.currentRow()
            del self._cameras[idx]
            self._refresh_camera_list()
    
    def _apply_settings(self):
        """Ayarları tətbiq edir."""
        # UI
        lang_map_inv = {'Azərbaycanca': 'az', 'English': 'en', 'Русский': 'ru'}
        language = lang_map_inv.get(self.language_combo.currentText(), 'en')
        
        self._config['ui'] = {
            'theme': self.theme_combo.currentText().lower(),
            'language': language
        }
        
        # AI
        self._config['ai'] = {
            'motion_threshold': self.motion_threshold_spin.value(),
            'face_confidence_threshold': self.face_confidence_spin.value(),
            'reid_confidence_threshold': self.reid_confidence_spin.value(),
            'detection_classes': ['person', 'cat', 'dog']
        }
        
        # Gait
        self._config['gait'] = {
            'enabled': self.gait_enabled_check.isChecked(),
            'threshold': self.gait_threshold_spin.value(),
            'sequence_length': self.gait_sequence_spin.value()
        }
        
        # Telegram
        self._config['telegram'] = {
            'bot_token': self.telegram_token_edit.text(),
            'chat_id': self.telegram_chat_edit.text()
        }
        
        # GSM
        com_port_text = self.gsm_port_combo.currentText()
        if com_port_text and ' ' in com_port_text:
            com_port = com_port_text.split()[0]
        elif com_port_text:
            com_port = com_port_text
        else:
            com_port = 'COM3'  # Default
        
        self._config['gsm'] = {
            'enabled': self.gsm_enabled_check.isChecked(),
            'com_port': self.gsm_port_combo.currentData() or com_port,
            'baud_rate': 9600,
            'phone_number': self.gsm_phone_edit.text()
        }
        
        # Storage
        self._config['storage'] = {
            'max_size_gb': self.max_storage_spin.value(),
            'recordings_path': './data/logs/',
            'faces_path': './data/faces/',
            'fifo_check_interval_minutes': self.cleanup_interval_spin.value()
        }
        
        # Save
        save_config(self._config)
        save_cameras(self._cameras)
        
        # Trigger live language update
        lang_map_inv = {'Azərbaycanca': 'az', 'English': 'en', 'Русский': 'ru'}
        new_language = lang_map_inv.get(self.language_combo.currentText(), 'en')
        set_language(new_language)
        
        self.settings_saved.emit()
        logger.info("Settings saved")
    
    def _save_and_close(self):
        """Ayarları saxla və bağla."""
        self._apply_settings()
        self.accept()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dialog = SettingsDialog()
    dialog.show()
    
    sys.exit(app.exec())
