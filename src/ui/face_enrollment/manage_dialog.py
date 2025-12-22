"""
FacePro Manage Faces Dialog
Mövcud üzləri idarə etmək üçün dialog.
"""

import os
import glob
from typing import List

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QListWidget, QListWidgetItem, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt

from src.utils.logger import get_logger
from src.ui.styles import DARK_THEME, COLORS
from .widgets import PersonCardWidget
from .enrollment_dialog import FaceEnrollmentDialog
from src.core.database.repositories.user_repository import UserRepository
from src.core.database.repositories.embedding_repository import EmbeddingRepository

logger = get_logger()

FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'faces')


class ManageFacesDialog(QDialog):
    """Mövcud üzləri idarə etmək üçün dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._user_repo = UserRepository()
        self._setup_ui()
        self._load_persons()
    
    def _setup_ui(self):
        self.setWindowTitle("👥 Şəxsləri İdarə Et")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("👥 Şəxsləri İdarə Et")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['text_primary']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
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
            QPushButton:hover {{ background-color: #27ae60; }}
        """)
        add_btn.clicked.connect(self._add_person)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {COLORS['bg_dark']}; }}")
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
        # Footer
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
            QPushButton:hover {{ background-color: {COLORS['bg_medium']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _load_persons(self):
        # Clear existing cards (except the stretch at the end)
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            # Fetch from repo
            rows = self._user_repo.get_users_with_stats()
            
            for user_id, name, face_count, body_count in rows:
                face_images = self._get_face_images(name)
                
                card = PersonCardWidget(user_id, name, face_count, body_count, face_images)
                # Use lambda capturing to pass parameters correctly
                card.add_face_clicked.connect(lambda uid=user_id, nm=name: self._add_face_to_person(uid, nm))
                card.add_body_clicked.connect(lambda uid=user_id, nm=name: self._add_body_to_person(uid, nm))
                card.edit_faces_clicked.connect(lambda uid=user_id, nm=name: self._edit_faces(uid, nm))
                card.edit_bodies_clicked.connect(lambda uid=user_id, nm=name: self._edit_bodies(uid, nm))
                card.delete_clicked.connect(lambda uid=user_id: self._delete_person(uid))
                
                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            
        except Exception as e:
            logger.error(f"Failed to load persons: {e}")
    
    def _get_face_images(self, name: str) -> List[str]:
        """User-in folder-indən 3 şəkil götürür."""
        user_dir = os.path.join(FACES_DIR, name)
        if not os.path.exists(user_dir):
            return []
        
        # Get jpg files
        files = glob.glob(os.path.join(user_dir, "*.jpg"))
        # Sort by modification time (newest first)
        files.sort(key=os.path.getmtime, reverse=True)
        return files[:3]
    
    def _add_person(self):
        """Yeni şəxs əlavə et (FaceEnrollmentDialog)"""
        dialog = FaceEnrollmentDialog(parent=self)
        if dialog.exec():
            self._load_persons()
            
    def _add_face_to_person(self, user_id: int, name: str):
        """Mövcud şəxsə üz əlavə et"""
        # Burada FaceEnrollmentDialog-u elə çağırmalıyıq ki, mövcud user-ə əlavə etsin.
        # Amma FaceEnrollmentDialog hazırda yeni user yaradır.
        # Sadəlik üçün eyni dialogu açıb, istifadəçinin adını avtomatik doldura bilərik.
        # Lakin FaceEnrollmentDialog-un arxitekturasına baxsaq, o UserRepository ilə işləyir.
        # Əgər ad eynidirsə, UserRepository.create_user mövcud ID-ni qaytarır (bunu yoxlamışdıq).
        # Ona görə də sadəcə dialoqu açmaq və adı ötürmək kifayətdir.
        
        dialog = FaceEnrollmentDialog(parent=self)
        # TODO: Dialog-a pre-fill name imkanı əlavə etmək olar, amma hələlik boş açırıq.
        # İstifadəçi adı seçməlidir. Ya da gələcəkdə bu hissəni təkmilləşdirərik.
        if dialog.exec():
            self._load_persons()

    def _add_body_to_person(self, user_id: int, name: str):
        QMessageBox.information(self, "Məlumat", 
            "Bədən (Re-ID) məlumatları kamera qarşısında avtomatik toplanır.\n"
            "Zəhmət olmasa həmin şəxsin kamerada görünməsini təmin edin."
        )

    def _edit_faces(self, user_id: int, name: str):
        dialog = EditEncodingsDialog(user_id, name, "face", parent=self)
        dialog.exec()
        self._load_persons()

    def _edit_bodies(self, user_id: int, name: str):
        dialog = EditEncodingsDialog(user_id, name, "body", parent=self)
        dialog.exec()
        self._load_persons()

    def _delete_person(self, user_id: int):
        reply = QMessageBox.question(
            self, "Sil",
            "Bu şəxsi və bütün məlumatlarını silmək istədiyinizə əminsiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._user_repo.delete_user(user_id):
                self._load_persons()
            else:
                QMessageBox.warning(self, "Xəta", "Silinmə zamanı xəta baş verdi.")


class EditEncodingsDialog(QDialog):
    """Üz və ya bədən encoding-lərini düzəltmək üçün dialog."""
    
    def __init__(self, user_id: int, name: str, encoding_type: str, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.name = name
        self.encoding_type = encoding_type
        self._embedding_repo = EmbeddingRepository()
        
        self._setup_ui()
        self._load_encodings()
    
    def _setup_ui(self):
        title = "Üzləri Düzəlt" if self.encoding_type == "face" else "Bədənləri Düzəlt"
        self.setWindowTitle(f"{title} - {self.name}")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        
        header = QLabel(f"{self.name} - {title}")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(header)
        
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
            QPushButton:hover {{ background-color: #c0392b; }}
        """)
        delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Bağla")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_encodings(self):
        self.encodings_list.clear()
        table = "face_encodings" if self.encoding_type == "face" else "reid_embeddings"
        
        try:
            ids = self._embedding_repo.get_embedding_ids(table, self.user_id)
            
            for i, enc_id in enumerate(ids, 1):
                label = f"Üz #{i}" if self.encoding_type == "face" else f"Bədən #{i}"
                item = QListWidgetItem(f"{label} (ID: {enc_id})")
                item.setData(Qt.ItemDataRole.UserRole, enc_id)
                self.encodings_list.addItem(item)
            
        except Exception as e:
            logger.error(f"Failed to load encodings: {e}")
    
    def _delete_selected(self):
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
            try:
                if self._embedding_repo.delete_embedding(table, enc_id):
                    self._load_encodings()
                else:
                    QMessageBox.warning(self, "Xəta", "Silinmə uğursuz oldu.")
            except Exception as e:
                logger.error(f"Failed to delete encoding: {e}")
