"""
FacePro Video Widget Module
Video stream göstərmək üçün custom PyQt6 widget.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

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

from PyQt6.QtWidgets import QLabel, QSizePolicy, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor, QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.helpers import cv2_to_qpixmap
from src.ui.styles import COLORS


class VideoWidget(QLabel):
    """
    Video stream göstərmək üçün custom widget.
    
    Signals:
        clicked: Widget-ə klik edildikdə
        double_clicked: Widget-ə double-klik edildikdə
    """
    
    clicked = pyqtSignal()
    double_clicked = pyqtSignal()
    
    def __init__(self, camera_name: str = "Camera", parent=None):
        """
        Args:
            camera_name: Kamera adı (overlay-də göstərilir)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.camera_name = camera_name
        self._is_connected = False
        self._show_overlay = True
        self._fps = 0
        self._last_frame_time = 0
        self._frame_count = 0
        
        # Widget setup
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_medium']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        
        # Default placeholder
        self._show_placeholder()
        
        # FPS hesablama üçün timer
        self._fps_timer = QTimer(self)
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(1000)  # Hər saniyə
    
    def _show_placeholder(self):
        """Placeholder görüntü göstərir."""
        self.setText(f"📷 {self.camera_name}\n\nConnecting...")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_medium']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                color: {COLORS['text_secondary']};
                font-size: 14px;
            }}
        """)
    
    def update_frame(self, frame: np.ndarray):
        """
        Yeni frame göstərir.
        
        Args:
            frame: BGR frame (OpenCV format)
        """
        if frame is None:
            return
        
        try:
            # Widget ölçüsünə uyğunlaşdır
            target_size = (self.width() - 4, self.height() - 4)  # Border üçün -4
            
            # QPixmap-a çevir
            pixmap = cv2_to_qpixmap(frame, target_size)
            
            if not pixmap.isNull():
                self.setPixmap(pixmap)
                self._frame_count += 1
                self._is_connected = True
                
        except Exception as e:
            print(f"Frame update error: {e}")
    
    def _update_fps(self):
        """FPS hesablayır."""
        self._fps = self._frame_count
        self._frame_count = 0
    
    def set_connected(self, connected: bool):
        """
        Bağlantı statusunu ayarlar.
        
        Args:
            connected: Bağlıdırmı?
        """
        self._is_connected = connected
        
        if not connected:
            self._show_placeholder()
    
    def set_overlay_visible(self, visible: bool):
        """Overlay görünüşünü ayarlar."""
        self._show_overlay = visible
    
    def get_fps(self) -> int:
        """Cari FPS-i qaytarır."""
        return self._fps
    
    def set_drawing_mode(self, enabled: bool):
        """Drawing rejimini aktivləşdirir."""
        self._drawing_mode = enabled
        self._roi_points = []
        self._normalized_roi_points = []
        self.setMouseTracking(enabled)
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_roi_points(self, points: list):
        """Mövcud ROI nöqtələrini təyin edir (metod qəbul edir: [(x, y), ...])."""
        self._normalized_roi_points = points
        self.update()

    def get_roi_points(self) -> list:
        """Normalizasiya olunmuş ROI nöqtələrini qaytarır."""
        return self._normalized_roi_points

    def mousePressEvent(self, event):
        """Mouse click event handler."""
        if getattr(self, '_drawing_mode', False):
            if event.button() == Qt.MouseButton.LeftButton:
                pos = event.position()
                x = pos.x()
                y = pos.y()
                
                # Normalizasiya olunmuş koordinatları hesabla
                norm_x = x / self.width()
                norm_y = y / self.height()
                
                self._roi_points.append((x, y))
                self._normalized_roi_points.append((norm_x, norm_y))
                self.update()
                
            elif event.button() == Qt.MouseButton.RightButton:
                # Sağ klik ilə son nöqtəni sil
                if self._roi_points:
                    self._roi_points.pop()
                    self._normalized_roi_points.pop()
                    self.update()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Mouse release event handler."""
        if not getattr(self, '_drawing_mode', False):
            if event.button() == Qt.MouseButton.LeftButton:
                self.clicked.emit()
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Mouse double-click event handler."""
        if not getattr(self, '_drawing_mode', False):
            if event.button() == Qt.MouseButton.LeftButton:
                self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)
        
    def paintEvent(self, event):
        """Paint event override - ROI çəkmək üçün."""
        super().paintEvent(event)
        
        # Əgər ROI nöqtələri varsa, çək
        points = getattr(self, '_normalized_roi_points', [])
        if points:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Koordinatları pikselə çevir
            pixel_points = []
            w, h = self.width(), self.height()
            
            from PyQt6.QtCore import QPoint
            
            for nx, ny in points:
                pixel_points.append(QPoint(int(nx * w), int(ny * h)))
                
            # Poliqon çək
            if len(pixel_points) > 1:
                painter.setPen(QColor(0, 255, 0, 200))  # Yaşıl xətt
                painter.setBrush(QColor(0, 255, 0, 50)) # Şəffaf yaşıl
                painter.drawPolygon(pixel_points)
                
            # Nöqtələri çək
            painter.setBrush(QColor(255, 0, 0)) # Qırmızı nöqtələr
            painter.setPen(Qt.PenStyle.NoPen)
            for p in pixel_points:
                painter.drawEllipse(p, 4, 4)


class VideoGrid(QWidget):
    """
    Çoxlu kamera üçün grid görünüşü.
    """
    
    camera_selected = pyqtSignal(str)  # camera_name
    
    def __init__(self, parent=None):
        """
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._widgets: dict[str, VideoWidget] = {}
        self._layout = None
        self._columns = 2  # Default 2x2 grid
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI setup."""
        from PyQt6.QtWidgets import QGridLayout
        
        self._layout = QGridLayout(self)
        self._layout.setSpacing(10)
        self._layout.setContentsMargins(10, 10, 10, 10)
    
    def add_camera_view(self, camera_name: str) -> VideoWidget:
        """
        Yeni kamera görünüşü əlavə edir.
        
        Args:
            camera_name: Kamera adı
            
        Returns:
            Yaradılan VideoWidget
        """
        if camera_name in self._widgets:
            return self._widgets[camera_name]
        
        widget = VideoWidget(camera_name)
        widget.clicked.connect(lambda: self.camera_selected.emit(camera_name))
        
        # Grid-ə əlavə et
        count = len(self._widgets)
        row = count // self._columns
        col = count % self._columns
        
        self._layout.addWidget(widget, row, col)
        self._widgets[camera_name] = widget
        
        return widget
    
    def remove_camera_view(self, camera_name: str):
        """Kamera görünüşünü silir."""
        if camera_name in self._widgets:
            widget = self._widgets.pop(camera_name)
            self._layout.removeWidget(widget)
            widget.deleteLater()
            self._reorganize_grid()
    
    def get_widget(self, camera_name: str) -> Optional[VideoWidget]:
        """Kamera widget-ini qaytarır."""
        return self._widgets.get(camera_name)
    
    def update_frame(self, camera_name: str, frame: np.ndarray):
        """
        Kamera frame-ini yeniləyir.
        
        Args:
            camera_name: Kamera adı
            frame: BGR frame
        """
        widget = self._widgets.get(camera_name)
        if widget:
            widget.update_frame(frame)
    
    def set_columns(self, columns: int):
        """Grid sütun sayını ayarlar."""
        self._columns = max(1, columns)
        self._reorganize_grid()
    
    def _reorganize_grid(self):
        """Grid-i yenidən təşkil edir."""
        # Bütün widget-ləri çıxar
        for widget in self._widgets.values():
            self._layout.removeWidget(widget)
        
        # Yenidən əlavə et
        for i, (name, widget) in enumerate(self._widgets.items()):
            row = i // self._columns
            col = i % self._columns
            self._layout.addWidget(widget, row, col)
    
    def clear_all(self):
        """Bütün kamera görünüşlərini silir."""
        for name in list(self._widgets.keys()):
            widget = self._widgets.pop(name)
            self._layout.removeWidget(widget)
            widget.deleteLater()
    
    @property
    def camera_names(self) -> list:
        """Kamera adlarının siyahısı."""
        return list(self._widgets.keys())


class StatusIndicator(QWidget):
    """
    Status indikatoru widget-i (dairəvi LED).
    """
    
    def __init__(self, size: int = 12, parent=None):
        """
        Args:
            size: İndikator ölçüsü (px)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._size = size
        self._color = QColor(COLORS['offline'])
        
        self.setFixedSize(size, size)
    
    def set_status(self, status: str):
        """
        Status ayarlar.
        
        Args:
            status: 'online', 'offline', 'warning', 'error'
        """
        color_map = {
            'online': COLORS['online'],
            'connected': COLORS['online'],
            'offline': COLORS['offline'],
            'disconnected': COLORS['offline'],
            'warning': COLORS['warning'],
            'error': COLORS['danger'],
        }
        
        self._color = QColor(color_map.get(status.lower(), COLORS['unknown']))
        self.update()
    
    def paintEvent(self, event):
        """Paint event - dairə çəkir."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dairə
        painter.setBrush(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(1, 1, self._size - 2, self._size - 2)


if __name__ == "__main__":
    # Test
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Single video widget test
    widget = VideoWidget("Test Camera")
    widget.setFixedSize(640, 480)
    widget.show()
    
    # Test frame
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    cv2.putText(test_frame, "Test Frame", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Update test
    timer = QTimer()
    timer.timeout.connect(lambda: widget.update_frame(test_frame))
    timer.start(33)  # ~30 FPS
    
    sys.exit(app.exec())
