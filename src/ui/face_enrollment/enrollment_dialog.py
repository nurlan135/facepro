"""
FacePro Face Enrollment Dialog
Dialog for adding new known faces to the system.
"""

import os
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

import cv2
import numpy as np

from src.utils.logger import get_logger
from src.utils.helpers import ensure_dir
from src.ui.styles import DARK_THEME, COLORS
from src.utils.i18n import tr
from .widgets import FacePreviewWidget

logger = get_logger()

FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'faces')


class FaceEnrollmentDialog(QDialog):
    """Dialog for adding a new known face."""
    
    face_enrolled = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._face_recognition = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle(tr('enroll_title'))
        self.setMinimumSize(600, 450)
        self.setProperty("class", "dialog_window")
        self.setStyleSheet(DARK_THEME + """
            QDialog {
                background-color: #121212;
            }
            QLabel {
                color: #e2e8f0;
            }
            QLineEdit {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 10px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            /* Clean Panel Style to replace GroupBox */
            QFrame[class="panel"] {
                background-color: #1a1c23;
                border: 1px solid #2d3748;
                border-radius: 12px;
                padding: 15px;
            }
            QLabel[class="panel_title"] {
                font-size: 14px;
                font-weight: bold;
                color: #a0aec0;
                margin-bottom: 10px;
            }
            QPushButton[class="action_btn"] {
                background-color: #2d3748; 
                color: white;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 8px 16px;
            }
            QPushButton[class="action_btn"]:hover {
                background-color: #4a5568;
            }
            QPushButton[class="primary_btn"] {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton[class="primary_btn"]:hover {
                background-color: #2563EB;
            }
            QPushButton[class="primary_btn"]:disabled {
                background-color: #4a5568;
                color: #a0aec0;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header = QLabel(tr('enroll_subtitle'))
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        main_layout.addWidget(header)
        
        # Content Area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # --- Left Panel: Image Preview ---
        left_panel = QFrame()
        left_panel.setProperty("class", "panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_img_title = QLabel(tr('enroll_group_image'))
        lbl_img_title.setProperty("class", "panel_title")
        left_layout.addWidget(lbl_img_title)
        
        self.face_preview = FacePreviewWidget()
        self.face_preview.setMinimumSize(220, 220)
        # Style the preview widget container if needed, mostly handled internally
        left_layout.addWidget(self.face_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        
        left_layout.addSpacing(10)
        
        # Image Buttons
        browse_btn = QPushButton(f"📂 {tr('enroll_btn_select')}")
        browse_btn.setProperty("class", "action_btn")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_image)
        left_layout.addWidget(browse_btn)
        
        capture_btn = QPushButton(f"📷 {tr('enroll_btn_capture')}")
        capture_btn.setProperty("class", "action_btn")
        capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        capture_btn.clicked.connect(self._capture_from_webcam)
        left_layout.addWidget(capture_btn)
        
        content_layout.addWidget(left_panel, 1) # Stretch factor 1
        
        # --- Right Panel: Details Form ---
        right_panel = QFrame()
        right_panel.setProperty("class", "panel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_details_title = QLabel(tr('enroll_group_details'))
        lbl_details_title.setProperty("class", "panel_title")
        right_layout.addWidget(lbl_details_title)
        
        right_layout.addSpacing(10)
        
        # Form Layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Name
        lbl_name = QLabel(tr('enroll_field_name'))
        lbl_name.setStyleSheet("font-weight: bold;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr('enroll_placeholder_name'))
        form_layout.addRow(lbl_name, self.name_edit)
        
        # Role
        lbl_role = QLabel(tr('enroll_field_role'))
        lbl_role.setStyleSheet("font-weight: bold;")
        self.role_edit = QLineEdit()
        self.role_edit.setPlaceholderText(tr('enroll_placeholder_role'))
        form_layout.addRow(lbl_role, self.role_edit)
        
        # Notes
        lbl_notes = QLabel(tr('enroll_field_notes'))
        lbl_notes.setStyleSheet("font-weight: bold;")
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText(tr('enroll_placeholder_notes'))
        form_layout.addRow(lbl_notes, self.notes_edit)
        
        right_layout.addLayout(form_layout)
        
        right_layout.addStretch()
        
        # Status Label area
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: rgba(255,255,255,0.05); border-radius: 8px; padding: 10px;")
        sf_layout = QHBoxLayout(status_frame)
        sf_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel(tr('enroll_field_status'))
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #a0aec0; font-size: 13px;")
        sf_layout.addWidget(self.status_label)
        
        right_layout.addWidget(status_frame)
        
        content_layout.addWidget(right_panel, 2) # Stretch factor 2
        
        main_layout.addLayout(content_layout)
        
        # Footer Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(tr('enroll_btn_cancel'))
        cancel_btn.setProperty("class", "action_btn")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        self.save_btn = QPushButton(tr('enroll_btn_save'))
        self.save_btn.setProperty("class", "primary_btn")
        self.save_btn.setMinimumWidth(150)
        self.save_btn.clicked.connect(self._save_face)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(btn_layout)

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr('enroll_btn_select'), "",
            "Images (*.jpg *.jpeg *.png *.bmp);;All Files (*)"
        )
        if path:
            self._load_and_validate_image(path)
    
    def _load_and_validate_image(self, path: str):
        if not self.face_preview.load_image(path):
            self.status_label.setText(tr('enroll_error_load'))
            self.status_label.setStyleSheet("color: #FC8181;") # Red-300
            self.save_btn.setEnabled(False)
            return
        
        self.status_label.setText(tr('enroll_status_checking'))
        self.status_label.setStyleSheet("color: #F6E05E;") # Yellow-300
        self.repaint()
        
        cv_image = self.face_preview.get_cv_image()
        face_count = self._detect_faces(cv_image)
        
        if face_count == 0:
            self.status_label.setText(tr('enroll_status_no_face'))
            self.status_label.setStyleSheet("color: #FC8181;") # Red
            self.save_btn.setEnabled(False)
        elif face_count == 1:
            self.status_label.setText(tr('enroll_status_one_face'))
            self.status_label.setStyleSheet("color: #68D391;") # Green-300
            self.save_btn.setEnabled(True)
        else:
            msg = tr('enroll_status_multi_face').replace('{count}', str(face_count))
            self.status_label.setText(msg)
            self.status_label.setStyleSheet("color: #F6E05E;") # Yellow
            self.save_btn.setEnabled(False)
    
    def _detect_faces(self, image: np.ndarray) -> int:
        try:
            if self._face_recognition is None:
                import face_recognition
                self._face_recognition = face_recognition
            
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_locations = self._face_recognition.face_locations(rgb)
            return len(face_locations)
        except ImportError:
            logger.warning("face_recognition not available")
            return 1
        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return 0
    
    def _capture_from_webcam(self):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                QMessageBox.warning(self, "Error", "Could not open webcam")
                return
            
            help_msg = tr('enroll_capture_help')
            QMessageBox.information(self, "Capture", 
                f"{help_msg}\n\nClick OK to open webcam preview.")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                cv2.imshow(f"Capture Face - {help_msg}", frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == 27: # ESC
                    break
                elif key == 32: # SPACE
                    ensure_dir(FACES_DIR)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    capture_path = os.path.join(FACES_DIR, f"capture_{timestamp}.jpg")
                    cv2.imwrite(capture_path, frame)
                    
                    cap.release()
                    cv2.destroyAllWindows()
                    self._load_and_validate_image(capture_path)
                    return
            
            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            logger.error(f"Webcam capture failed: {e}")
            QMessageBox.critical(self, "Error", f"Webcam capture failed: {e}")
    
    def _save_face(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", tr('enroll_error_no_name'))
            return
        
        cv_image = self.face_preview.get_cv_image()
        if cv_image is None:
            QMessageBox.warning(self, "Error", tr('enroll_error_no_image'))
            return
        
        try:
            if self._face_recognition is None:
                import face_recognition
                self._face_recognition = face_recognition
            
            rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            face_encodings = self._face_recognition.face_encodings(rgb)
            
            if not face_encodings:
                QMessageBox.critical(self, "Error", "Could not extract face encoding.")
                return
            
            encoding = face_encodings[0]
            
            ensure_dir(FACES_DIR)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in name if c.isalnum() or c in "_ -")
            image_filename = f"{safe_name}_{timestamp}.jpg"
            image_path = os.path.join(FACES_DIR, image_filename)
            
            h, w = cv_image.shape[:2]
            max_size = 640
            if max(h, w) > max_size:
                scale = max_size / max(h, w)
                new_size = (int(w * scale), int(h * scale))
                cv_image = cv2.resize(cv_image, new_size)
            
            cv2.imwrite(image_path, cv_image)
            self._save_to_database(name, encoding, image_path)
            
            logger.info(f"Face enrolled: {name} -> {image_path}")
            self.face_enrolled.emit(name, image_path)
            
            msg = tr('enroll_success_msg').replace('{name}', name)
            QMessageBox.information(self, tr('enroll_success_title'), msg)
            self.accept()
            
        except ImportError:
            QMessageBox.critical(self, "Error", 
                "face_recognition library is not installed.\nPlease run: pip install face_recognition")
        except Exception as e:
            logger.error(f"Failed to save face: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save face: {e}")
    
    def _save_to_database(self, name: str, encoding: np.ndarray, image_path: str):
        import sqlite3
        from src.utils.helpers import get_db_path
        import pickle
        
        db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                user_id = existing[0]
            else:
                cursor.execute("INSERT INTO users (name, created_at) VALUES (?, datetime('now'))", (name,))
                user_id = cursor.lastrowid
            
            encoding_blob = pickle.dumps(encoding)
            cursor.execute("INSERT INTO face_encodings (user_id, encoding) VALUES (?, ?)", (user_id, encoding_blob))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            raise
