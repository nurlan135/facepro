"""
FacePro Face Enrollment Dialog
Dialog for adding new known faces to the system.
"""

import os
import cv2
import numpy as np
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QMessageBox, QFrame, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt6.QtGui import QImage, QPixmap

from src.utils.logger import get_logger
from src.utils.helpers import ensure_dir, cv2_to_qpixmap
from src.ui.styles import COLORS, CYBER_THEME
from src.utils.i18n import tr
from src.core.database.repositories.user_repository import UserRepository
from src.core.database.repositories.embedding_repository import EmbeddingRepository
from src.core.face_recognizer import FaceRecognizer
from src.core.services.face_quality_service import FaceQualityService

logger = get_logger()

FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'faces')


class CameraWorker(QThread):
    """Temporary camera thread for enrollment."""
    frame_captured = pyqtSignal(np.ndarray)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._running = False

    def run(self):
        self._running = True
        cap = cv2.VideoCapture(self.camera_index)
        while self._running:
            ret, frame = cap.read()
            if ret:
                self.frame_captured.emit(frame)
            QThread.msleep(30)
        cap.release()

    def stop(self):
        self._running = False
        self.wait()


class FaceEnrollmentDialog(QDialog):
    """Dialog for adding a new known face."""
    
    face_enrolled = pyqtSignal(str, str)
    
    def __init__(self, parent=None, camera_index=0):
        super().__init__(parent)
        self.camera_index = camera_index
        
        # Repositories & Engine
        self._user_repo = UserRepository()
        self._embedding_repo = EmbeddingRepository()
        self._face_recognizer = FaceRecognizer()
        self._quality_service = FaceQualityService()
        
        # State
        self._current_frame: Optional[np.ndarray] = None
        self._captured_image: Optional[np.ndarray] = None
        self._camera_worker: Optional[CameraWorker] = None
        self._face_encoding: Optional[np.ndarray] = None
        
        self._setup_ui()
        self._start_camera()
        
    def _setup_ui(self):
        self.setWindowTitle("Yeni Üz Əlavə Et")
        self.setFixedSize(600, 750)
        self.setStyleSheet(CYBER_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background: {COLORS.get('bg_panel', '#000')}; border-bottom: 1px solid {COLORS.get('border_tech', '#333')};")
        header_layout = QHBoxLayout(header_widget)
        
        title = QLabel("Yeni Şəxs Qeydiyyatı")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLORS.get('cyber_cyan', '#0FF')}; letter-spacing: 1px;")
        header_layout.addWidget(title)
        
        layout.addWidget(header_widget)
        
        # Preview Area
        self.preview_lbl = QLabel()
        self.preview_lbl.setFixedSize(480, 360)
        self.preview_lbl.setStyleSheet(f"""
            background-color: black; 
            border: 1px solid {COLORS.get('border_tech', '#333')};
        """)
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        preview_container = QHBoxLayout()
        preview_container.addStretch()
        preview_container.addWidget(self.preview_lbl)
        preview_container.addStretch()
        layout.addLayout(preview_container)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_capture = QPushButton("📷 Şəkil Çək")
        self.btn_capture.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_capture.setStyleSheet(self._btn_style(COLORS.get('cyber_cyan', '#0FF'), text_color='black'))
        self.btn_capture.clicked.connect(self._capture_frame)
        
        self.btn_upload = QPushButton("📂 Fayl Yüklə")
        self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload.setStyleSheet(self._btn_style(COLORS.get('bg_panel', '#333'), text_color=COLORS.get('text_main', '#FFF'), border=True))
        self.btn_upload.clicked.connect(self._upload_file)
        
        self.btn_retake = QPushButton("🔄")
        self.btn_retake.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retake.setStyleSheet(self._btn_style(COLORS.get('alert_red', '#F00')))
        self.btn_retake.clicked.connect(self._retake)
        self.btn_retake.hide()
        
        btn_layout.addWidget(self.btn_capture)
        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_retake)
        layout.addLayout(btn_layout)
        
        # Form
        form_frame = QFrame()
        form_frame.setStyleSheet(f"background-color: rgba(255,255,255,0.05); border-radius: 4px; padding: 15px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ad və Soyad")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(0,0,0,0.3);
                padding: 10px;
                border: 1px solid {COLORS.get('border_tech', '#333')};
                border-radius: 4px;
                color: {COLORS.get('text_main', '#FFF')};
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS.get('cyber_cyan', '#0FF')};
            }}
        """)
        
        lbl_name = QLabel("Ad Soyad:")
        lbl_name.setStyleSheet(f"color: {COLORS.get('text_main', '#FFF')}; font-weight: bold;")
        
        form_layout.addRow(lbl_name, self.name_input)
        layout.addWidget(form_frame)
        
        # Status Label
        self.status_lbl = QLabel("Kamera aktivdir...")
        self.status_lbl.setStyleSheet(f"color: {COLORS.get('text_muted', '#888')}; font-style: italic; font-family: 'Consolas';")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)
        
        # Action Buttons
        actions_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Bağla")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS.get('border_tech', '#333')};
                color: {COLORS.get('text_muted', '#888')};
                padding: 10px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                color: {COLORS.get('text_main', '#FFF')};
                border-color: {COLORS.get('text_main', '#FFF')};
            }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Yadda Saxla")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet(self._btn_style(COLORS.get('acid_green', '#0F0'), text_color='black'))
        self.btn_save.clicked.connect(self._save)
        self.btn_save.setEnabled(False)
        
        actions_layout.addWidget(self.btn_cancel)
        actions_layout.addWidget(self.btn_save)
        layout.addLayout(actions_layout)

    def _btn_style(self, bg_color, text_color="white", border=False):
        border_str = f"border: 1px solid {COLORS.get('cyber_cyan', '#0FF')};" if border else "border: none;"
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                {border_str}
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-family: 'Rajdhani', sans-serif;
                font-size: 14px;
            }}
            QPushButton:hover {{ opacity: 0.8; }}
            QPushButton:disabled {{ background-color: rgba(255,255,255,0.1); color: rgba(255,255,255,0.3); border: none; }}
        """

    def _start_camera(self):
        self._camera_worker = CameraWorker(self.camera_index)
        self._camera_worker.frame_captured.connect(self._update_preview)
        self._camera_worker.start()

    def _stop_camera(self):
        if self._camera_worker:
            try:
                self._camera_worker.frame_captured.disconnect(self._update_preview)
            except:
                pass
            self._camera_worker.stop()
            self._camera_worker = None

    def _update_preview(self, frame: np.ndarray):
        self._current_frame = frame
        pixmap = cv2_to_qpixmap(frame, (480, 360))
        self.preview_lbl.setPixmap(pixmap)

    def _capture_frame(self):
        if self._current_frame is not None:
            self._process_image(self._current_frame.copy())

    def _upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Şəkil Seç", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            try:
                # Windows Unicode path fix
                with open(path, "rb") as f:
                    chunk = f.read()
                chunk_arr = np.frombuffer(chunk, dtype=np.uint8)
                img = cv2.imdecode(chunk_arr, cv2.IMREAD_UNCHANGED)
                
                if img is not None:
                    # Remove alpha channel if png
                    if img.shape[2] == 4:
                        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                        
                    self._stop_camera()
                    self._process_image(img)
            except Exception as e:
                logger.error(f"Image load error: {e}")

    def _process_image(self, image: np.ndarray):
        self._captured_image = image
        self._stop_camera()
        
        # Show static image
        pixmap = cv2_to_qpixmap(image, (480, 360))
        self.preview_lbl.setPixmap(pixmap)
        
        # AI Processing (Detect Face)
        self.status_lbl.setText("Üz emal edilir...")
        self.status_lbl.setStyleSheet(f"color: {COLORS.get('cyber_gold', '#f39c12')};")
        QThread.msleep(100) # UX delay
        
        try:
            # 1. Detect faces
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            encodings = self._face_recognizer.get_encodings(rgb)
            
            if len(encodings) == 0:
                self.status_lbl.setText("❌ Üz tapılmadı! Zəhmət olmasa yenidən cəhd edin.")
                self.status_lbl.setStyleSheet(f"color: {COLORS.get('alert_red', '#e74c3c')};")
                self._enable_retake(True)
                return
            
            if len(encodings) > 1:
                self.status_lbl.setText("⚠️ Birdən çox üz tapıldı! Yalnız bir nəfər olmalıdır.")
                self.status_lbl.setStyleSheet(f"color: {COLORS.get('cyber_gold', '#f39c12')};")
                self._enable_retake(True)
                return
            
            # 2. Quality Check
            is_good, q_msg, q_score = self._quality_service.check_quality(image)
            if not is_good:
                self.status_lbl.setText(f"❌ {q_msg}")
                self.status_lbl.setStyleSheet(f"color: {COLORS.get('alert_red', '#e74c3c')};")
                self._enable_retake(True)
                return
                
            self._face_encoding = encodings[0]
            self.status_lbl.setText(f"✅ Üz aşkarlandı! (Keyfiyyət score: {q_score:.0f})")
            self.status_lbl.setStyleSheet(f"color: {COLORS.get('acid_green', '#2ecc71')};")
            
            self._enable_retake(True)
            self.btn_save.setEnabled(True)
            self.name_input.setFocus()
            
        except Exception as e:
            logger.error(f"Face processing error: {e}")
            self.status_lbl.setText("Xəta baş verdi.")

    def _enable_retake(self, enable: bool):
        self.btn_capture.hide()
        self.btn_upload.hide()
        self.btn_retake.show()

    def _retake(self):
        self._captured_image = None
        self._face_encoding = None
        self.btn_retake.hide()
        self.btn_capture.show()
        self.btn_upload.show()
        self.btn_save.setEnabled(False)
        self.status_lbl.setText("Kamera aktivdir...")
        self.status_lbl.setStyleSheet("color: #aaa;")
        self._start_camera()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Xəta", "Zəhmət olmasa ad və soyad daxil edin.")
            return
        
        if self._face_encoding is None:
            return

        try:
            # 1. Şəkli diskə yaz
            ensure_dir(FACES_DIR)
            safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
            user_dir = os.path.join(FACES_DIR, safe_name)
            ensure_dir(user_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"face_{timestamp}.jpg"
            filepath = os.path.join(user_dir, filename)
            
            cv2.imwrite(filepath, self._captured_image)
            
            # 2. DB-yə yaz
            self._save_to_database(name, self._face_encoding, filepath)
            
            # Audit Log
            from src.utils.audit_logger import get_audit_logger
            get_audit_logger().log("FACE_ENROLLED", {"name": name, "path": filepath})
            
            QMessageBox.information(self, "Uğurlu", "Şəxs uğurla əlavə edildi!")
            self.accept()
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            QMessageBox.critical(self, "Xəta", f"Yadda saxlamaq mümkün olmadı:\n{e}")

    def _save_to_database(self, name: str, encoding: np.ndarray, image_path: str):
        # Create user (or get existing ID)
        user_id = self._user_repo.create_user(name)
        if not user_id:
            raise Exception("Failed to get or create user ID")
        
        # Save face encoding
        if self._embedding_repo.add_face_encoding(user_id, encoding):
            logger.info(f"Face encoding saved for user: {name}")
        else:
            raise Exception("Failed to save face encoding")

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)
