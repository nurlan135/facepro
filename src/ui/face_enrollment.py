"""
FacePro Face Enrollment Dialog Module
Yeni üzləri sistemə əlavə etmək üçün dialog.
"""

import os
from typing import Optional, List
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QListWidget, QListWidgetItem, QGroupBox,
    QFrame, QSizePolicy, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QAction, QMouseEvent

import cv2
import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import ensure_dir
from src.ui.styles import DARK_THEME, COLORS

logger = get_logger()

# Faces folder path
FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'faces')


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
            # OpenCV ilə oxu
            self._cv_image = cv2.imread(path)
            
            if self._cv_image is None:
                return False
            
            self._image_path = path
            
            # Resize for preview
            h, w = self._cv_image.shape[:2]
            scale = min(196 / w, 196 / h)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(self._cv_image, (new_w, new_h))
            
            # BGR to RGB
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # QPixmap yaratmaq
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
        """OpenCV formatında şəkli qaytarır."""
        return self._cv_image
    
    def get_image_path(self) -> Optional[str]:
        """Şəkil yolunu qaytarır."""
        return self._image_path
    
    def clear_image(self):
        """Şəkli təmizləyir."""
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


class FaceEnrollmentDialog(QDialog):
    """
    Yeni üz əlavə etmək üçün dialog.
    
    Signals:
        face_enrolled: Yeni üz uğurla əlavə edildikdə (name, image_path)
    """
    
    face_enrolled = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._face_recognition = None
        self._setup_ui()
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle("Add Known Face")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Add a New Known Face")
        header.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
        """)
        layout.addWidget(header)
        
        # Content
        content_layout = QHBoxLayout()
        
        # Left side - Image preview
        preview_group = QGroupBox("Face Image")
        preview_layout = QVBoxLayout(preview_group)
        
        self.face_preview = FacePreviewWidget()
        preview_layout.addWidget(self.face_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Browse button
        browse_btn = QPushButton("Select Image...")
        browse_btn.clicked.connect(self._browse_image)
        preview_layout.addWidget(browse_btn)
        
        # Capture button (from webcam)
        capture_btn = QPushButton("Capture from Webcam")
        capture_btn.setProperty("class", "secondary")
        capture_btn.clicked.connect(self._capture_from_webcam)
        preview_layout.addWidget(capture_btn)
        
        content_layout.addWidget(preview_group)
        
        # Right side - Details
        details_group = QGroupBox("Person Details")
        details_layout = QFormLayout(details_group)
        details_layout.setSpacing(15)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter person's name")
        details_layout.addRow("Name:", self.name_edit)
        
        # Role (optional)
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText("e.g., Family, Employee, Guest")
        details_layout.addRow("Role:", self.role_edit)
        
        # Notes
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes...")
        details_layout.addRow("Notes:", self.notes_edit)
        
        # Face detection status
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        details_layout.addRow("Status:", self.status_label)
        
        content_layout.addWidget(details_group)
        
        layout.addLayout(content_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton("Save Face")
        self.save_btn.clicked.connect(self._save_face)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def _browse_image(self):
        """Şəkil faylı seçmək."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Face Image", "",
            "Images (*.jpg *.jpeg *.png *.bmp);;All Files (*)"
        )
        
        if path:
            self._load_and_validate_image(path)
    
    def _load_and_validate_image(self, path: str):
        """Şəkli yükləyir və üz olub-olmadığını yoxlayır."""
        if not self.face_preview.load_image(path):
            self.status_label.setText("❌ Failed to load image")
            self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
            self.save_btn.setEnabled(False)
            return
        
        # Üz aşkarlaması
        self.status_label.setText("🔍 Checking for face...")
        self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
        self.repaint()
        
        cv_image = self.face_preview.get_cv_image()
        face_count = self._detect_faces(cv_image)
        
        if face_count == 0:
            self.status_label.setText("❌ No face detected in image")
            self.status_label.setStyleSheet(f"color: {COLORS['danger']};")
            self.save_btn.setEnabled(False)
        elif face_count == 1:
            self.status_label.setText("✅ Face detected!")
            self.status_label.setStyleSheet(f"color: {COLORS['online']};")
            self.save_btn.setEnabled(True)
        else:
            self.status_label.setText(f"⚠️ {face_count} faces detected. Please use an image with only one face.")
            self.status_label.setStyleSheet(f"color: {COLORS['warning']};")
            self.save_btn.setEnabled(False)
    
    def _detect_faces(self, image: np.ndarray) -> int:
        """Şəkildə üz sayını qaytarır."""
        try:
            # Lazy load face_recognition
            if self._face_recognition is None:
                import face_recognition
                self._face_recognition = face_recognition
            
            # BGR to RGB
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = self._face_recognition.face_locations(rgb)
            
            return len(face_locations)
            
        except ImportError:
            logger.warning("face_recognition not available, skipping face detection")
            return 1  # Assume there's a face
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return 0
    
    def _capture_from_webcam(self):
        """Webcam-dan şəkil çəkmək."""
        try:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                QMessageBox.warning(self, "Error", "Could not open webcam")
                return
            
            # Preview window
            QMessageBox.information(
                self, "Capture", 
                "Press SPACE to capture, ESC to cancel.\n\nClick OK to open webcam preview."
            )
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Show preview
                cv2.imshow("Capture Face - SPACE to capture, ESC to cancel", frame)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == 27:  # ESC
                    break
                elif key == 32:  # SPACE
                    # Save captured frame
                    ensure_dir(FACES_DIR)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    capture_path = os.path.join(FACES_DIR, f"capture_{timestamp}.jpg")
                    cv2.imwrite(capture_path, frame)
                    
                    cap.release()
                    cv2.destroyAllWindows()
                    
                    # Load the captured image
                    self._load_and_validate_image(capture_path)
                    return
            
            cap.release()
            cv2.destroyAllWindows()
            
        except Exception as e:
            logger.error(f"Webcam capture failed: {e}")
            QMessageBox.critical(self, "Error", f"Webcam capture failed: {e}")
    
    def _save_face(self):
        """Üzü sistemə saxlayır."""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name for this person.")
            return
        
        cv_image = self.face_preview.get_cv_image()
        if cv_image is None:
            QMessageBox.warning(self, "Error", "Please select an image first.")
            return
        
        try:
            # Lazy load face_recognition
            if self._face_recognition is None:
                import face_recognition
                self._face_recognition = face_recognition
            
            # Get face encoding
            rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            face_encodings = self._face_recognition.face_encodings(rgb)
            
            if not face_encodings:
                QMessageBox.critical(self, "Error", "Could not extract face encoding.")
                return
            
            encoding = face_encodings[0]
            
            # Save image to faces folder
            ensure_dir(FACES_DIR)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in name if c.isalnum() or c in "_ -")
            image_filename = f"{safe_name}_{timestamp}.jpg"
            image_path = os.path.join(FACES_DIR, image_filename)
            
            # Copy or save image
            original_path = self.face_preview.get_image_path()
            if original_path and os.path.exists(original_path):
                # Resize and save
                h, w = cv_image.shape[:2]
                max_size = 640
                if max(h, w) > max_size:
                    scale = max_size / max(h, w)
                    new_size = (int(w * scale), int(h * scale))
                    cv_image = cv2.resize(cv_image, new_size)
            
            cv2.imwrite(image_path, cv_image)
            
            # Save to database
            self._save_to_database(name, encoding, image_path)
            
            logger.info(f"Face enrolled: {name} -> {image_path}")
            
            # Emit signal
            self.face_enrolled.emit(name, image_path)
            
            QMessageBox.information(
                self, "Success", 
                f"Face for '{name}' has been saved successfully!"
            )
            
            self.accept()
            
        except ImportError:
            QMessageBox.critical(
                self, "Error", 
                "face_recognition library is not installed.\n"
                "Please run: pip install face_recognition"
            )
        except Exception as e:
            logger.error(f"Failed to save face: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save face: {e}")
    
    def _save_to_database(self, name: str, encoding: np.ndarray, image_path: str):
        """Üz məlumatlarını database-ə saxlayır."""
        import sqlite3
        from src.utils.helpers import get_db_path
        import pickle
        
        db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 1. users cədvəlinə əlavə et (name UNIQUE-dir)
            # Əvvəlcə eyni adlı user varmı yoxla
            cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                user_id = existing[0]
            else:
                cursor.execute("""
                    INSERT INTO users (name, created_at)
                    VALUES (?, datetime('now'))
                """, (name,))
                user_id = cursor.lastrowid
            
            # 2. face_encodings cədvəlinə əlavə et
            encoding_blob = pickle.dumps(encoding)
            
            cursor.execute("""
                INSERT INTO face_encodings (user_id, encoding)
                VALUES (?, ?)
            """, (user_id, encoding_blob))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved to database: user_id={user_id}, name={name}")
            
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            raise


class PersonCardWidget(QFrame):
    """Şəxs kartı widget-i - üz və bədən məlumatları ilə."""
    
    add_face_clicked = pyqtSignal(int, str)  # user_id, name
    add_body_clicked = pyqtSignal(int, str)  # user_id, name
    edit_faces_clicked = pyqtSignal(int, str)  # user_id, name
    edit_bodies_clicked = pyqtSignal(int, str)  # user_id, name
    delete_clicked = pyqtSignal(int, str)  # user_id, name
    
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
        
        # Header row: Name + counts + buttons (all in one line like image 2)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Name label (bold, larger)
        name_label = QLabel(self.name)
        name_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            background: transparent;
        """)
        header_layout.addWidget(name_label)
        
        # Counts (smaller, colored)
        counts_label = QLabel(f"{self.face_count} üz | {self.body_count} bədən")
        counts_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['success']};
            background: transparent;
            padding-left: 10px;
        """)
        header_layout.addWidget(counts_label)
        
        header_layout.addStretch()
        
        # Action buttons - all in header row
        add_face_btn = QPushButton("+ Üz Əlavə Et")
        add_face_btn.setFixedHeight(30)
        add_face_btn.setStyleSheet(f"""
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
        """)
        add_face_btn.clicked.connect(lambda: self.add_face_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(add_face_btn)
        
        add_body_btn = QPushButton("🧍 Bədən Əlavə Et")
        add_body_btn.setFixedHeight(30)
        add_body_btn.setStyleSheet(f"""
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
        """)
        add_body_btn.clicked.connect(lambda: self.add_body_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(add_body_btn)
        
        edit_bodies_btn = QPushButton(f"✏ Bədənləri Düzəlt ({self.body_count})")
        edit_bodies_btn.setFixedHeight(30)
        edit_bodies_btn.setStyleSheet(f"""
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
        """)
        edit_bodies_btn.clicked.connect(lambda: self.edit_bodies_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(edit_bodies_btn)
        
        edit_faces_btn = QPushButton("✏ Üzləri Düzəlt")
        edit_faces_btn.setFixedHeight(30)
        edit_faces_btn.setStyleSheet(f"""
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
        """)
        edit_faces_btn.clicked.connect(lambda: self.edit_faces_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(edit_faces_btn)
        
        delete_btn = QPushButton("🗑 Şəxsi Sil")
        delete_btn.setFixedHeight(30)
        delete_btn.setStyleSheet(f"""
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
        """)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.user_id, self.name))
        header_layout.addWidget(delete_btn)
        
        layout.addLayout(header_layout)
        
        # Face thumbnails row - larger thumbnails like image 2
        thumbs_layout = QHBoxLayout()
        thumbs_layout.setSpacing(3)
        thumbs_layout.setContentsMargins(0, 5, 0, 0)
        
        for img_path in self.face_images[:5]:  # Max 5 thumbnails
            thumb = self._create_thumbnail(img_path)
            if thumb:
                thumbs_layout.addWidget(thumb)
        
        thumbs_layout.addStretch()
        layout.addLayout(thumbs_layout)
    
    def _create_thumbnail(self, image_path: str) -> Optional[QLabel]:
        """Thumbnail yaradır - sağ klik ilə silmək mümkündür."""
        try:
            if not os.path.exists(image_path):
                return None
            
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # Larger thumbnail size like image 2
            h, w = img.shape[:2]
            size = 80  # Bigger thumbnails
            scale = size / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(img, (new_w, new_h))
            
            # BGR to RGB
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            
            # QPixmap
            h, w, ch = rgb.shape
            q_image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            
            label = ClickableImageLabel(image_path, self)
            label.setPixmap(pixmap)
            label.setFixedSize(size, size)
            label.setScaledContents(True)
            label.setStyleSheet(f"""
                border: 2px solid transparent;
                border-radius: 3px;
                background: transparent;
            """)
            label.setToolTip("Sağ klik - silmək üçün")
            label.image_deleted.connect(self._on_image_deleted)
            
            return label
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            return None
    
    def _on_image_deleted(self, image_path: str):
        """Şəkil silindikdə yenilə."""
        # Remove from list
        if image_path in self.face_images:
            self.face_images.remove(image_path)
        
        # Find and remove the widget
        sender = self.sender()
        if sender:
            sender.deleteLater()


class ManageFacesDialog(QDialog):
    """Mövcud üzləri idarə etmək üçün dialog - şəkildəki kimi detallı."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_persons()
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle("👥 Şəxsləri İdarə Et")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("👥 Şəxsləri İdarə Et")
        title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Add new person button
        add_btn = QPushButton("+ Yeni Şəxs Əlavə Et")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """)
        add_btn.clicked.connect(self._add_person)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll area for person cards
        from PyQt6.QtWidgets import QScrollArea, QWidget
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['bg_dark']};
            }}
        """)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
        # Footer buttons
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("Bağla")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 30px;
                color: {COLORS['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_medium']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _load_persons(self):
        """Database-dən şəxsləri yükləyir."""
        import sqlite3
        from src.utils.helpers import get_db_path
        
        # Clear existing cards
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all users with face and body counts
            cursor.execute("""
                SELECT u.id, u.name,
                       (SELECT COUNT(*) FROM face_encodings WHERE user_id = u.id) as face_count,
                       (SELECT COUNT(*) FROM reid_embeddings WHERE user_id = u.id) as body_count
                FROM users u
                ORDER BY u.name
            """)
            
            for row in cursor.fetchall():
                user_id = row['id']
                name = row['name']
                face_count = row['face_count']
                body_count = row['body_count']
                
                # Get face images for thumbnails
                face_images = self._get_face_images(user_id, name)
                
                # Create card
                card = PersonCardWidget(user_id, name, face_count, body_count, face_images)
                card.add_face_clicked.connect(self._add_face_to_person)
                card.add_body_clicked.connect(self._add_body_to_person)
                card.edit_faces_clicked.connect(self._edit_faces)
                card.edit_bodies_clicked.connect(self._edit_bodies)
                card.delete_clicked.connect(self._delete_person)
                
                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load persons: {e}")
    
    def _get_face_images(self, user_id: int, name: str) -> List[str]:
        """Şəxsin üz şəkillərini qaytarır - ada görə filtrlənmiş."""
        images = []
        if os.path.exists(FACES_DIR):
            # Adı normallaşdır (fayl adında istifadə edilən formata çevir)
            safe_name = "".join(c for c in name if c.isalnum() or c in "_ -").lower()
            
            for f in os.listdir(FACES_DIR):
                if f.endswith(('.jpg', '.jpeg', '.png')):
                    # Fayl adının şəxsin adı ilə başlayıb-başlamadığını yoxla
                    file_lower = f.lower()
                    name_lower = name.lower().replace(" ", "_")
                    
                    if file_lower.startswith(safe_name) or file_lower.startswith(name_lower):
                        images.append(os.path.join(FACES_DIR, f))
                        if len(images) >= 5:
                            break
        return images
    
    def _add_person(self):
        """Yeni şəxs əlavə et."""
        dialog = FaceEnrollmentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_persons()
    
    def _add_face_to_person(self, user_id: int, name: str):
        """Mövcud şəxsə üz əlavə et."""
        dialog = FaceEnrollmentDialog(self)
        dialog.name_edit.setText(name)
        dialog.name_edit.setEnabled(False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_persons()
    
    def _add_body_to_person(self, user_id: int, name: str):
        """Mövcud şəxsə bədən əlavə et."""
        QMessageBox.information(self, "Bədən Əlavə Et", 
            f"'{name}' üçün bədən əlavə etmə funksiyası.\n\n"
            "Bu funksiya avtomatik Re-ID enrollment ilə işləyir.\n"
            "Şəxs kamera qarşısında durduqda sistem avtomatik bədən embedding-i saxlayır.")
    
    def _edit_faces(self, user_id: int, name: str):
        """Şəxsin üzlərini düzəlt."""
        dialog = EditEncodingsDialog(user_id, name, "face", self)
        dialog.exec()
        self._load_persons()
    
    def _edit_bodies(self, user_id: int, name: str):
        """Şəxsin bədənlərini düzəlt."""
        dialog = EditEncodingsDialog(user_id, name, "body", self)
        dialog.exec()
        self._load_persons()
    
    def _delete_person(self, user_id: int, name: str):
        """Şəxsi sil."""
        reply = QMessageBox.question(
            self, "Şəxsi Sil",
            f"'{name}' adlı şəxsi silmək istədiyinizə əminsiniz?\n\n"
            "Bu əməliyyat bütün üz və bədən məlumatlarını siləcək.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_from_database(user_id)
            self._load_persons()
    
    def _delete_from_database(self, user_id: int):
        """Database-dən şəxsi silir."""
        import sqlite3
        from src.utils.helpers import get_db_path
        
        db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM face_encodings WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM reid_embeddings WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM gait_embeddings WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted user_id={user_id} from database")
            
        except Exception as e:
            logger.error(f"Failed to delete from database: {e}")


class EditEncodingsDialog(QDialog):
    """Üz və ya bədən encoding-lərini düzəltmək üçün dialog."""
    
    def __init__(self, user_id: int, name: str, encoding_type: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.name = name
        self.encoding_type = encoding_type  # "face" or "body"
        
        self._setup_ui()
        self._load_encodings()
    
    def _setup_ui(self):
        title = "Üzləri Düzəlt" if self.encoding_type == "face" else "Bədənləri Düzəlt"
        self.setWindowTitle(f"{title} - {self.name}")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"{self.name} - {title}")
        header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(header)
        
        # List
        self.encodings_list = QListWidget()
        self.encodings_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
            }}
        """)
        layout.addWidget(self.encodings_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        delete_btn = QPushButton("Seçilmişi Sil")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
        """)
        delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Bağla")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_encodings(self):
        """Encoding-ləri yükləyir."""
        import sqlite3
        from src.utils.helpers import get_db_path
        
        self.encodings_list.clear()
        
        table = "face_encodings" if self.encoding_type == "face" else "reid_embeddings"
        
        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT id FROM {table} WHERE user_id = ?", (self.user_id,))
            
            for i, row in enumerate(cursor.fetchall(), 1):
                enc_id = row[0]
                label = f"Üz #{i}" if self.encoding_type == "face" else f"Bədən #{i}"
                
                item = QListWidgetItem(f"{label} (ID: {enc_id})")
                item.setData(Qt.ItemDataRole.UserRole, enc_id)
                self.encodings_list.addItem(item)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load encodings: {e}")
    
    def _delete_selected(self):
        """Seçilmiş encoding-i silir."""
        item = self.encodings_list.currentItem()
        if not item:
            return
        
        enc_id = item.data(Qt.ItemDataRole.UserRole)
        table = "face_encodings" if self.encoding_type == "face" else "reid_embeddings"
        
        reply = QMessageBox.question(
            self, "Sil",
            "Bu encoding-i silmək istədiyinizə əminsiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import sqlite3
            from src.utils.helpers import get_db_path
            
            try:
                conn = sqlite3.connect(get_db_path())
                conn.execute(f"DELETE FROM {table} WHERE id = ?", (enc_id,))
                conn.commit()
                conn.close()
                
                self._load_encodings()
                
            except Exception as e:
                logger.error(f"Failed to delete encoding: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dialog = FaceEnrollmentDialog()
    dialog.show()
    
    sys.exit(app.exec())
