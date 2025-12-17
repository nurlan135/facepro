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
    """Şəxs kartı widget-i - üz və bədən məlumatları ilə."""
    
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
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }}
            QFrame:hover {{
                border-color: {COLORS['border_light']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        name_label = QLabel(self.name)
        name_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(name_label)
        
        counts_label = QLabel(f"{self.face_count} üz | {self.body_count} bədən")
        counts_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['success']};
            background: transparent;
            padding-left: 10px;
        """)
        header_layout.addWidget(counts_label)
        
        header_layout.addStretch()
        
        # Action buttons
        add_face_btn = QPushButton("+ Üz Əlavə Et")
        add_face_btn.setFixedHeight(30)
        add_face_btn.setStyleSheet(self._get_outline_btn_style())
        add_face_btn.clicked.connect(lambda: self.add_face_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(add_face_btn)
        
        add_body_btn = QPushButton("🧍 Bədən Əlavə Et")
        add_body_btn.setFixedHeight(30)
        add_body_btn.setStyleSheet(self._get_outline_btn_style())
        add_body_btn.clicked.connect(lambda: self.add_body_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(add_body_btn)
        
        edit_bodies_btn = QPushButton(f"✏ Bədənləri Düzəlt ({self.body_count})")
        edit_bodies_btn.setFixedHeight(30)
        edit_bodies_btn.setStyleSheet(self._get_success_btn_style())
        edit_bodies_btn.clicked.connect(lambda: self.edit_bodies_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(edit_bodies_btn)
        
        edit_faces_btn = QPushButton("✏ Üzləri Düzəlt")
        edit_faces_btn.setFixedHeight(30)
        edit_faces_btn.setStyleSheet(self._get_primary_btn_style())
        edit_faces_btn.clicked.connect(lambda: self.edit_faces_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(edit_faces_btn)
        
        delete_btn = QPushButton("🗑 Şəxsi Sil")
        delete_btn.setFixedHeight(30)
        delete_btn.setStyleSheet(self._get_danger_btn_style())
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Face thumbnails row
        thumbs_layout = QHBoxLayout()
        thumbs_layout.setSpacing(3)
        thumbs_layout.setContentsMargins(0, 5, 0, 0)
        
        for img_path in self.face_images[:5]:
            thumb = self._create_thumbnail(img_path)
            if thumb:
                thumbs_layout.addWidget(thumb)
        
        thumbs_layout.addStretch()
        layout.addLayout(thumbs_layout)
    
    def _get_outline_btn_style(self):
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
                padding: 5px 12px;
                color: {COLORS['text_secondary']};
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['text_primary']};
                color: {COLORS['text_primary']};
            }}
        """
    
    def _get_primary_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                border: none;
                border-radius: 5px;
                padding: 5px 12px;
                color: white;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """
    
    def _get_success_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {COLORS['success']};
                border: none;
                border-radius: 5px;
                padding: 5px 12px;
                color: white;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """
    
    def _get_danger_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                border: none;
                border-radius: 5px;
                padding: 5px 12px;
                color: white;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
        """
    
    def _create_thumbnail(self, image_path: str) -> Optional[ClickableImageLabel]:
        try:
            if not os.path.exists(image_path):
                return None
            
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            h, w = img.shape[:2]
            size = 80
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
            label.setStyleSheet("border: 2px solid transparent; border-radius: 3px; background: transparent;")
            label.setToolTip("Sağ klik - silmək üçün")
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
