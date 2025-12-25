"""
FacePro Face Enrollment Widgets
Üz qeydiyyatı üçün yardımçı widget-lər.
"""

import os
from typing import Optional, List

from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

import cv2
import numpy as np

from src.utils.logger import get_logger
from src.ui.styles import COLORS
from src.utils.i18n import tr

logger = get_logger()


class ClickableImageLabel(QLabel):
    """Sağ klik ilə silmək mümkün olan şəkil label-i."""
    
    image_deleted = pyqtSignal(str)  # image_path
    
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                color: {COLORS['text_primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['danger']};
                border-radius: 3px;
            }}
        """)
        
        delete_action = menu.addAction("🗑 Şəkli Sil")
        action = menu.exec(self.mapToGlobal(pos))
        
        if action == delete_action:
            self._delete_image()
    
    def _delete_image(self):
        reply = QMessageBox.question(
            self, "Şəkli Sil",
            "Bu şəkli silmək istədiyinizə əminsiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.exists(self.image_path):
                    os.remove(self.image_path)
                    logger.info(f"Deleted image: {self.image_path}")
                    self.image_deleted.emit(self.image_path)
            except Exception as e:
                logger.error(f"Failed to delete image: {e}")
                QMessageBox.critical(self, "Xəta", f"Şəkil silinə bilmədi: {e}")


class FacePreviewWidget(QLabel):
    """Üz şəklini göstərmək üçün widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setFixedSize(200, 200)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_medium']};
                border: 2px dashed {COLORS['border']};
                border-radius: 8px;
                color: {COLORS['text_secondary']};
            }}
        """)
        self.setText("📷\nNo Image")
        
        self._image_path: Optional[str] = None
        self._cv_image: Optional[np.ndarray] = None
    
    def load_image(self, path: str) -> bool:
        """Şəkli yükləyir və göstərir."""
        try:
            self._cv_image = cv2.imread(path)
            
            if self._cv_image is None:
                return False
            
            self._image_path = path
            
            h, w = self._cv_image.shape[:2]
            scale = min(196 / w, 196 / h)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(self._cv_image, (new_w, new_h))
            
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            self.setPixmap(pixmap)
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {COLORS['bg_medium']};
                    border: 2px solid {COLORS['primary']};
                    border-radius: 8px;
                }}
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return False
    
    def get_cv_image(self) -> Optional[np.ndarray]:
        return self._cv_image
    
    def get_image_path(self) -> Optional[str]:
        return self._image_path
    
    def clear_image(self):
        self._image_path = None
        self._cv_image = None
        self.clear()
        self.setText("📷\nNo Image")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_medium']};
                border: 2px dashed {COLORS['border']};
                border-radius: 8px;
                color: {COLORS['text_secondary']};
            }}
        """)


class PersonCardWidget(QFrame):
    """Cyber-Brutalist Person Card Widget."""
    
    add_face_clicked = pyqtSignal(int, str)
    add_body_clicked = pyqtSignal(int, str)
    edit_faces_clicked = pyqtSignal(int, str)
    edit_bodies_clicked = pyqtSignal(int, str)
    delete_clicked = pyqtSignal(int, str)
    
    def __init__(self, user_id: int, name: str, face_count: int, body_count: int, 
                 face_images: List[str], parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.name = name
        self.face_count = face_count
        self.body_count = body_count
        self.face_images = face_images
        
        self._setup_ui()
    
    def _setup_ui(self):
        # Card Style
        cyan_color = COLORS.get('cyber_cyan', '#00F0FF')
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.03);
                border-left: 2px solid {cyan_color};
                margin-bottom: 8px;
                border-radius: 0px;
            }}
            QFrame:hover {{
                background-color: rgba(255, 255, 255, 0.08);
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # 1. Avatar (First Image)
        if self.face_images:
            thumb = self._create_thumbnail(self.face_images[0], size=48)
            if thumb:
                layout.addWidget(thumb)
            else:
                layout.addWidget(self._create_placeholder_avatar())
        else:
            layout.addWidget(self._create_placeholder_avatar())
            
        # 2. Info Block
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_lbl = QLabel(self.name)
        text_color = COLORS.get('text_main', '#E0E0E0')
        muted_color = COLORS.get('text_muted', '#6b7280')
        
        name_lbl.setStyleSheet(f"color: {text_color}; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        info_layout.addWidget(name_lbl)
        
        stats_text = f"FACES: {self.face_count} | BODIES: {self.body_count}"
        stats_lbl = QLabel(stats_text)
        stats_lbl.setStyleSheet(f"color: {muted_color}; font-size: 11px; font-family: 'Consolas'; border: none; background: transparent;")
        info_layout.addWidget(stats_lbl)
        
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # 3. Action Buttons (Right Aligned)
        
        # Add Face (Camera Icon)
        self._add_btn(layout, "📷", tr("enrollment.btn_capture"), 
                      lambda: self.add_face_clicked.emit(self.user_id, self.name), text_color)
        
        # Add Body (Person Icon)
        self._add_btn(layout, "🧍", "Add Body Data", 
                      lambda: self.add_body_clicked.emit(self.user_id, self.name), text_color)
        
        # Edit Faces (Pencil Icon)
        self._add_btn(layout, "✏️", "Edit Faces", 
                      lambda: self.edit_faces_clicked.emit(self.user_id, self.name), cyan_color)

        if self.body_count > 0:
            self._add_btn(layout, "🧬", "Edit Body Data", 
                          lambda: self.edit_bodies_clicked.emit(self.user_id, self.name), COLORS.get('acid_green', '#CCFF00'))
        
        # Delete (Trash Icon)
        self._add_btn(layout, "🗑️", tr("user_management.delete"), 
                      lambda: self.delete_clicked.emit(self.user_id, self.name), COLORS.get('alert_red', '#FF3300'))

    def _add_btn(self, layout, icon, tooltip, callback, color):
        btn = QPushButton(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(callback)
        
        border_col = "rgba(255, 255, 255, 0.1)"
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid {border_col};
                border-radius: 4px;
                color: {color};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border-color: {color};
            }}
        """)
        layout.addWidget(btn)
        
    def _create_placeholder_avatar(self):
        lbl = QLabel("👤")
        lbl.setFixedSize(48, 48)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"background: rgba(255,255,255,0.05); border-radius: 4px; font-size: 20px; color: {COLORS.get('text_muted', '#888')}; border: none;")
        return lbl

    def _create_thumbnail(self, image_path: str, size=48) -> Optional[ClickableImageLabel]:
        try:
            if not os.path.exists(image_path):
                return None
            
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            h, w = img.shape[:2]
            scale = size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(img, (new_w, new_h))
            
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            q_image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            label = ClickableImageLabel(image_path, self)
            label.setPixmap(pixmap)
            label.setFixedSize(size, size)
            label.setScaledContents(True)
            label.setStyleSheet("border: 1px solid rgba(255,255,255,0.2); border-radius: 2px; background: transparent;")
            label.setToolTip("Right click to delete")
            label.image_deleted.connect(self._on_image_deleted)
            
            return label
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            return None
    
    def _on_image_deleted(self, image_path: str):
        if image_path in self.face_images:
            self.face_images.remove(image_path)
        sender = self.sender()
        if sender:
            sender.deleteLater()
