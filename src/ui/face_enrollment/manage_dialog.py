"""
FacePro Manage Faces Dialog
Mövcud üzləri idarə etmək üçün dialog.
"""

import os
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

logger = get_logger()

FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data', 'faces')


class ManageFacesDialog(QDialog):
    """Mövcud üzləri idarə etmək üçün dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        import sqlite3
        from src.utils.helpers import get_db_path
        
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
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
                
                face_images = self._get_face_images(user_id, name)
                
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
        images = []
        if os.path.exists(FACES_DIR):
            safe_name = "".join(c for c in name if c.isalnum() or c in "_ -").lower()
            
            for f in os.listdir(FACES_DIR):
                if f.endswith(('.jpg', '.jpeg', '.png')):
                    file_lower = f.lower()
                    name_lower = name.lower().replace(" ", "_")
                    
                    if file_lower.startswith(safe_name) or file_lower.startswith(name_lower):
                        images.append(os.path.join(FACES_DIR, f))
                        if len(images) >= 5:
                            break
        return images
    
    def _add_person(self):
        dialog = FaceEnrollmentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_persons()
    
    def _add_face_to_person(self, user_id: int, name: str):
        dialog = FaceEnrollmentDialog(self)
        dialog.name_edit.setText(name)
        dialog.name_edit.setEnabled(False)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_persons()
    
    def _add_body_to_person(self, user_id: int, name: str):
        QMessageBox.information(self, "Bədən Əlavə Et", 
            f"'{name}' üçün bədən əlavə etmə funksiyası.\n\n"
            "Bu funksiya avtomatik Re-ID enrollment ilə işləyir.")
    
    def _edit_faces(self, user_id: int, name: str):
        dialog = EditEncodingsDialog(user_id, name, "face", self)
        dialog.exec()
        self._load_persons()
    
    def _edit_bodies(self, user_id: int, name: str):
        dialog = EditEncodingsDialog(user_id, name, "body", self)
        dialog.exec()
        self._load_persons()
    
    def _delete_person(self, user_id: int, name: str):
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
        import sqlite3
        from src.utils.helpers import get_db_path
        
        try:
            conn = sqlite3.connect(get_db_path())
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
        self.encoding_type = encoding_type
        
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
