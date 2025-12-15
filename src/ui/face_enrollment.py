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
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

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


class ManageFacesDialog(QDialog):
    """Mövcud üzləri idarə etmək üçün dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._load_faces()
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle("Manage Known Faces")
        self.setMinimumSize(600, 400)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Known Faces")
        header.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
        """)
        layout.addWidget(header)
        
        # Faces list
        self.faces_list = QListWidget()
        self.faces_list.setStyleSheet(f"""
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
        layout.addWidget(self.faces_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add New Face")
        add_btn.clicked.connect(self._add_face)
        btn_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setProperty("class", "danger")
        delete_btn.clicked.connect(self._delete_face)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "secondary")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_faces(self):
        """Database-dən üzləri yükləyir."""
        import sqlite3
        
        from src.utils.helpers import get_db_path
        
        db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.name, u.created_at
                FROM users u
                ORDER BY u.created_at DESC
            """)
            
            self.faces_list.clear()
            
            for row in cursor.fetchall():
                user_id, name, created_at = row
                display_date = created_at[:10] if created_at else 'Unknown'
                
                item = QListWidgetItem(f"{name} - Added: {display_date}")
                item.setData(Qt.ItemDataRole.UserRole, user_id)
                self.faces_list.addItem(item)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to load faces: {e}")
    
    def _add_face(self):
        """Yeni üz əlavə etmək."""
        dialog = FaceEnrollmentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_faces()
    
    def _delete_face(self):
        """Seçilmiş üzü silmək."""
        item = self.faces_list.currentItem()
        if not item:
            return
        
        user_id = item.data(Qt.ItemDataRole.UserRole)
        name = item.text().split(" (")[0]
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._delete_from_database(user_id)
            self._load_faces()
    
    def _delete_from_database(self, user_id: int):
        """Database-dən üzü silir."""
        import sqlite3
        
        from src.utils.helpers import get_db_path
        
        db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Delete face encodings
            cursor.execute("DELETE FROM face_encodings WHERE user_id = ?", (user_id,))
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted user_id={user_id} from database")
            
        except Exception as e:
            logger.error(f"Failed to delete from database: {e}")


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dialog = FaceEnrollmentDialog()
    dialog.show()
    
    sys.exit(app.exec())
