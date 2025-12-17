"""
FacePro Local Camera Selector Dialog
Lokal kamera (webcam) seçim dialoqu.
"""

from typing import Optional, Dict, List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QTimer

import cv2

from src.ui.styles import COLORS, DARK_THEME
from src.ui.camera_preview import CameraPreviewThread, CameraCard
from src.utils.i18n import tr
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
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
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
        self.no_camera_label.setStyleSheet(f"font-size: 14px; color: {COLORS['text_muted']}; padding: 20px;")
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
