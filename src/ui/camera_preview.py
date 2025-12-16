"""
FacePro Camera Preview Module
Kamera önizləmə thread-i və kartı.
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np
import time

from src.ui.styles import COLORS, DARK_THEME
from src.utils.i18n import tr


class CameraPreviewThread(QThread):
    """Kamera önizləmə thread-i."""
    
    frame_ready = pyqtSignal(int, object)  # device_id, frame (numpy array)
    error = pyqtSignal(int, str)  # device_id, error_message
    info_ready = pyqtSignal(int, dict)  # device_id, camera_info
    
    def __init__(self, device_id: int, parent=None):
        super().__init__(parent)
        self._device_id = device_id
        self._running = False
        self._cap: Optional[cv2.VideoCapture] = None
    
    def run(self):
        """Preview loop - 500ms intervalda frame göndərir."""
        self._running = True
        
        try:
            # Kameranı aç
            self._cap = cv2.VideoCapture(self._device_id, cv2.CAP_DSHOW)
            
            if not self._cap.isOpened():
                self.error.emit(self._device_id, tr('camera_open_failed') if tr('camera_open_failed') != 'camera_open_failed' else "Kamera açıla bilmədi")
                return
            
            # Kamera məlumatlarını al
            width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self._cap.get(cv2.CAP_PROP_FPS)
            
            camera_info = {
                'device_id': self._device_id,
                'name': f"Camera {self._device_id}",
                'resolution': (width, height),
                'fps': fps if fps > 0 else 30.0,
                'backend': 'DSHOW'
            }
            self.info_ready.emit(self._device_id, camera_info)
            
            # Preview loop
            while self._running:
                ret, frame = self._cap.read()
                
                if ret and frame is not None:
                    # Frame-i kiçilt (preview üçün)
                    preview_frame = cv2.resize(frame, (160, 120))
                    self.frame_ready.emit(self._device_id, preview_frame)
                else:
                    self.error.emit(self._device_id, tr('frame_read_failed') if tr('frame_read_failed') != 'frame_read_failed' else "Frame oxuna bilmədi")
                
                # 500ms gözlə
                time.sleep(0.5)
                
        except Exception as e:
            self.error.emit(self._device_id, str(e))
        finally:
            self._release_camera()
    
    def _release_camera(self):
        """Kameranı azad edir."""
        if self._cap is not None:
            try:
                self._cap.release()
            except:
                pass
            self._cap = None
    
    def stop(self):
        """Thread-i dayandırır."""
        self._running = False
        self.wait(2000)  # Max 2 saniyə gözlə
        self._release_camera()


class CameraCard(QFrame):
    """Kamera önizləmə kartı."""
    
    selected = pyqtSignal(int, dict)  # device_id, camera_info
    
    PREVIEW_WIDTH = 160
    PREVIEW_HEIGHT = 120
    
    def __init__(self, device_id: int, parent=None):
        super().__init__(parent)
        self._device_id = device_id
        self._camera_info: Dict[str, Any] = {
            'device_id': device_id,
            'name': f"Camera {device_id}",
            'resolution': (0, 0),
            'fps': 0.0
        }
        self._setup_ui()
    
    def _setup_ui(self):
        """UI qurulumu."""
        self.setFixedSize(200, 220)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 2px solid {COLORS['border']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Preview label
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_dark']};
                border-radius: 6px;
                color: {COLORS['text_muted']};
            }}
        """)
        self.preview_label.setText("⏳")
        layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Info container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Camera name
        self.name_label = QLabel(f"Camera {self._device_id}")
        self.name_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.name_label)
        
        # Resolution & FPS
        self.resolution_label = QLabel("...")
        self.resolution_label.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        self.resolution_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.resolution_label)
        
        layout.addLayout(info_layout)
        
        # Select button
        self.select_btn = QPushButton(tr('select_this_camera') if tr('select_this_camera') != 'select_this_camera' else "Bu Kameranı Seç")
        self.select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        self.select_btn.clicked.connect(self._on_select)
        layout.addWidget(self.select_btn)
    
    def update_info(self, info: Dict[str, Any]):
        """Kamera məlumatlarını yeniləyir."""
        self._camera_info = info
        self.name_label.setText(info.get('name', f"Camera {self._device_id}"))
        
        res = info.get('resolution', (0, 0))
        fps = info.get('fps', 0)
        self.resolution_label.setText(f"{res[0]}x{res[1]} @ {fps:.0f} FPS")
    
    def update_preview(self, frame: np.ndarray):
        """Preview şəklini yeniləyir."""
        try:
            # BGR -> RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            # QImage yaratmaq
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Label-ə set etmək
            self.preview_label.setPixmap(pixmap.scaled(
                self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        except Exception as e:
            self.show_error(str(e))
    
    def show_error(self, message: str):
        """Xəta göstərir."""
        self.preview_label.setText("❌")
        self.preview_label.setToolTip(message)
        self.resolution_label.setText(message[:30] + "..." if len(message) > 30 else message)
        self.select_btn.setEnabled(False)
        self.select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['text_muted']};
                color: {COLORS['bg_dark']};
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 11px;
            }}
        """)
    
    def _on_select(self):
        """Kamera seçildikdə."""
        self.selected.emit(self._device_id, self._camera_info)
    
    def get_device_id(self) -> int:
        """Device ID qaytarır."""
        return self._device_id
