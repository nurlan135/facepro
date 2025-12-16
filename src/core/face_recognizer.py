"""
FacePro Face Recognition Module
dlib/face_recognition kitabxanası ilə üz tanıma.
"""

import os
from typing import Optional, Dict, List, Tuple

import cv2
import numpy as np

from src.utils.logger import get_logger
from src.utils.helpers import get_db_path

logger = get_logger()


class FaceRecognizer:
    """
    Face Recognition modulu.
    dlib/face_recognition kitabxanasını istifadə edir.
    """
    
    def __init__(self, tolerance: float = 0.6):
        """
        Args:
            tolerance: Face matching tolerance (aşağı = daha ciddi)
        """
        self._face_recognition = None
        self._tolerance = tolerance
        self._known_encodings: Dict[str, List[np.ndarray]] = {}  # {name: [encodings]}
        self._name_to_id: Dict[str, int] = {}  # {name: user_id}
        logger.info("FaceRecognizer created (lazy loading)")
    
    def _ensure_loaded(self):
        """face_recognition kitabxanasını yükləyir."""
        if self._face_recognition is not None:
            return
        
        try:
            import face_recognition
            self._face_recognition = face_recognition
            logger.info("face_recognition loaded")
        except ImportError as e:
            logger.error(f"face_recognition import failed: {e}")
            raise
    
    def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        """
        Tanınmış üz əlavə edir.
        
        Args:
            name: Şəxsin adı
            face_image: Üz şəkli (BGR)
            
        Returns:
            Uğurlu olub-olmadığı
        """
        try:
            self._ensure_loaded()
            
            # BGR -> RGB
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            
            # Encoding çıxar
            encodings = self._face_recognition.face_encodings(rgb_image)
            
            if not encodings:
                logger.warning(f"No face found in image for: {name}")
                return False
            
            if name not in self._known_encodings:
                self._known_encodings[name] = []
            
            self._known_encodings[name].append(encodings[0])
            logger.info(f"Face added for: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add face: {e}")
            return False
    
    def recognize(self, frame: np.ndarray, person_bbox: Tuple[int, int, int, int]) -> Tuple[Optional[str], Optional[int], float, bool]:
        """
        Frame-də üz tanıyır.
        
        Args:
            frame: Tam frame
            person_bbox: Şəxsin bounding box-u
            
        Returns:
            (ad, user_id, confidence, üz_görünürmü)
        """
        try:
            self._ensure_loaded()
            
            # Person bölgəsini kəs
            x1, y1, x2, y2 = person_bbox
            person_crop = frame[y1:y2, x1:x2]
            
            if person_crop.size == 0:
                return None, None, 0.0, False
            
            # RGB-ə çevir
            rgb_crop = cv2.cvtColor(person_crop, cv2.COLOR_BGR2RGB)
            
            # Üz yerini tap
            face_locations = self._face_recognition.face_locations(rgb_crop)
            
            if not face_locations:
                return None, None, 0.0, False  # Üz görünmür
            
            # Üz encoding-i çıxar
            face_encodings = self._face_recognition.face_encodings(rgb_crop, face_locations)
            
            if not face_encodings:
                return None, None, 0.0, True  # Üz var amma encoding çıxmadı
            
            # Tanınmış üzlərlə müqayisə
            best_match_name = None
            best_distance = float('inf')
            
            for name, known_encs in self._known_encodings.items():
                for known_enc in known_encs:
                    distance = self._face_recognition.face_distance([known_enc], face_encodings[0])[0]
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_match_name = name
            
            if best_match_name and best_distance <= self._tolerance:
                confidence = 1.0 - best_distance
                user_id = self._name_to_id.get(best_match_name)
                return best_match_name, user_id, confidence, True
            
            return None, None, 0.0, True  # Üz var amma tanınmadı
            
        except Exception as e:
            logger.error(f"Face recognition failed: {e}")
            return None, None, 0.0, False
    
    def load_from_database(self) -> int:
        """Database-dən bütün üzləri yükləyir."""
        import sqlite3
        import pickle
        
        db_path = get_db_path()
        if not os.path.exists(db_path):
            logger.warning("Database not found, no faces loaded")
            return 0
        
        loaded_count = 0
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.name, u.id, fe.encoding
                FROM users u
                JOIN face_encodings fe ON u.id = fe.user_id
            """)
            
            for name, user_id, encoding_blob in cursor.fetchall():
                try:
                    encoding = pickle.loads(encoding_blob)
                    
                    if name not in self._known_encodings:
                        self._known_encodings[name] = []
                    
                    self._known_encodings[name].append(encoding)
                    self._name_to_id[name] = user_id
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to load encoding for {name}: {e}")
            
            conn.close()
            
            logger.info(f"Loaded {loaded_count} face encodings from database")
            
        except Exception as e:
            logger.error(f"Failed to load faces from database: {e}")
        
        return loaded_count
    
    @property
    def known_count(self) -> int:
        """Tanınmış şəxs sayı."""
        return len(self._known_encodings)
    
    def get_user_id(self, name: str) -> Optional[int]:
        """Ad üzrə user_id qaytarır."""
        return self._name_to_id.get(name)
