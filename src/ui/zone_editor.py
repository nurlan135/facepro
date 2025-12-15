"""
FacePro Zone Editor Module
Kamera üçün ROI (Region of Interest) təyin etmək üçün dialog.
"""

from typing import Optional, Dict, List, Tuple
import cv2
import numpy as np

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QMessageBox
)
from PyQt6.QtCore import Qt

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.ui.video_widget import VideoWidget
from src.ui.styles import DARK_THEME, COLORS
from src.utils.helpers import build_rtsp_url, cv2_to_qpixmap
from src.utils.i18n import tr
from src.utils.logger import get_logger

logger = get_logger()

class ZoneEditorDialog(QDialog):
    """ROI redaktə dialoqu."""
    
    def __init__(self, camera_data: Dict, parent=None):
        super().__init__(parent)
        
        self._camera_data = camera_data
        self._roi_points = camera_data.get('roi_points', [])
        
        self._setup_ui()
        self._load_initial_image()
        
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle(tr('settings_title') + " - " + tr('lbl_classes')) # "Settings - Objects" (approx) or just "Zone Editor"
        self.setWindowTitle("Zone Editor")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instr_label = QLabel(
            "Sol klik: Nöqtə əlavə et\n"
            "Sağ klik: Son nöqtəni sil\n"
            "Capture Frame: Kameradan görüntü götür"
        )
        instr_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(instr_label)
        
        # Video Widget
        self.video_widget = VideoWidget()
        self.video_widget.set_drawing_mode(True)
        if self._roi_points:
            self.video_widget.set_roi_points(self._roi_points)
        layout.addWidget(self.video_widget, 1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        capture_btn = QPushButton("Capture Frame")
        capture_btn.clicked.connect(self._capture_frame)
        btn_layout.addWidget(capture_btn)
        
        clear_btn = QPushButton("Clear Zone")
        clear_btn.clicked.connect(self._clear_zone)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton(tr('btn_save'))
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(tr('btn_cancel'))
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def _get_source_url(self) -> str:
        """Kamera URL-ini qaytarır."""
        source = self._camera_data.get('source', '')
        # CameraDialog-da olduğu kimi tam URL artıq source-da ola bilər
        # Lakin settings faylında saxlanarkən "rtsp://..." kimi saxlanılır.
        # Əgər settings dialog-dan gəlirsə və hələ save olunmayıbsa, data strukturu fərqli ola bilər.
        # Amma biz SettingsDialog-da CameraDialog-dan aldığı datanı göndəririk.
        return source

    def _capture_frame(self, silent=False):
        """Kameradan bir frame götürür."""
        source = self._get_source_url()
        if not source:
            if not silent:
                QMessageBox.warning(self, "Error", "No source configured")
            return
            
        try:
            # Source int ola bilər (webcam)
            src = source
            # Əgər string-dirsə və rəqəmdən ibarətdirsə (məs: "0", "1"), int-ə çevir
            if isinstance(source, str) and source.isdigit():
                src = int(source)
                
            logger.info(f"ZoneEditor connecting to camera source: {src} (type: {type(src)})")
            
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) # Windows üçün CAP_DSHOW əlavə edirik (bəzən kömək edir)
            if not cap.isOpened():
                # DSHOW alınmasa, adi qaydada yoxla
                cap = cv2.VideoCapture(src)
            if not cap.isOpened():
                if not silent:
                    QMessageBox.warning(self, "Camera Error", 
                        "Kameraya qoşulmaq mümkün olmadı.\n"
                        "Əgər 'Start' basılıbsa, zəhmət olmasa sistemi dayandırın (Stop) və yenidən yoxlayın.\n"
                        "Windows-da webcam eyni anda yalnız bir yerdə işləyə bilər.")
                return
                
            # Kameranın istilənməsi üçün bir neçə frame burax
            for _ in range(5):
                cap.read()
                
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                self.video_widget.update_frame(frame)
            else:
                if not silent:
                    QMessageBox.warning(self, "Error", "Frame oxuna bilmədi.")
                
        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Error", f"Capture failed: {e}")
            
    def _load_initial_image(self):
        """Başlanğıc üçün cəhd edir."""
        # 500ms sonra avtomatik capture et
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, lambda: self._capture_frame(silent=True))
        
    def _clear_zone(self):
        """Zonanı təmizləyir."""
        self.video_widget.set_roi_points([])
        
    def _save(self):
        """Yadda saxlayır."""
        points = self.video_widget.get_roi_points()
        if len(points) > 0 and len(points) < 3:
            QMessageBox.warning(self, "Warning", "Zone must have at least 3 points")
            return
            
        self._roi_points = points
        self.accept()
        
    def get_roi_points(self) -> List[Tuple[float, float]]:
        """Qeyd olunmuş nöqtələri qaytarır."""
        return self._roi_points
