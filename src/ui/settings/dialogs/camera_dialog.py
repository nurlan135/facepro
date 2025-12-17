"""
FacePro Camera Dialog
Kamera əlavə etmə/redaktə dialoqu.
"""

from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QSpinBox, QComboBox, QFileDialog, QMessageBox
)

from src.ui.styles import DARK_THEME, COLORS
from src.utils.helpers import build_rtsp_url
from src.ui.zone_editor import ZoneEditorDialog


class CameraDialog(QDialog):
    """Kamera əlavə etmə/redaktə dialoqu."""
    
    def __init__(self, camera_data: Optional[Dict] = None, parent=None, preset_type: int = None):
        """
        Args:
            camera_data: Redaktə üçün mövcud kamera data-sı (None = yeni)
            parent: Parent widget
            preset_type: Əvvəlcədən seçilmiş kamera növü (0=RTSP, 1=Webcam)
        """
        super().__init__(parent)
        self._preset_type = preset_type
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
        
        # Connect URL update signals
        self.ip_edit.textChanged.connect(self._update_url)
        self.port_spin.valueChanged.connect(self._update_url)
        self.username_edit.textChanged.connect(self._update_url)
        self.password_edit.textChanged.connect(self._update_url)
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
        if self._preset_type is not None and not self._camera_data:
            self.type_combo.setCurrentIndex(self._preset_type)
            return
        
        if not self._camera_data:
            return
        
        self.name_edit.setText(self._camera_data.get('name', ''))
        
        source = self._camera_data.get('source', '')
        if source.startswith('rtsp'):
            self.type_combo.setCurrentIndex(0)
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
        self._update_url()
        temp_data = self._camera_data.copy()
        temp_data['source'] = self.url_edit.text()
        
        dialog = ZoneEditorDialog(temp_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._camera_data['roi_points'] = dialog.get_roi_points()
            QMessageBox.information(self, "Success", "Zone updated.")
