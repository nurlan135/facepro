"""
FacePro Face Recognition Module
dlib/face_recognition kitabxanası ilə üz tanıma.
"""

import os
from typing import Optional, Dict, List, Tuple

import cv2
import numpy as np

from src.utils.logger import get_logger
from src.utils.helpers import crop_person
from src.core.database.repositories.embedding_repository import EmbeddingRepository

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
        self._embedding_repo = EmbeddingRepository()
        logger.info("FaceRecognizer created (lazy loading)")

    def _load_library(self):
        """Lazy load face_recognition library."""
        if self._face_recognition is None:
            try:
                import face_recognition
                self._face_recognition = face_recognition
                logger.info("face_recognition library loaded")
            except ImportError:
                logger.error("face_recognition library not found!")
                raise

    def get_encodings(self, rgb_image: np.ndarray) -> List[np.ndarray]:
        """Şəkildən üz vektorlarını çıxarır."""
        self._load_library()
        # Find faces
        face_locations = self._face_recognition.face_locations(rgb_image)
        if not face_locations:
            return []
        
        # Compute encodings
        encodings = self._face_recognition.face_encodings(rgb_image, face_locations)
        return encodings

    def recognize(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Tuple[Optional[str], Optional[int], float, bool, Optional[Tuple]]:
        """
        Person bbox daxilində üz tanımağa çalışır.
        
        Returns:
            (name, user_id, confidence, face_visible, face_bbox)
        """
        self._load_library()
        
        # 1. Person crop
        person_img = crop_person(frame, bbox)
        if person_img is None or person_img.size == 0:
            return None, None, 0.0, False, None
            
        rgb_person = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGB)
        
        # 2. Detect face in crop
        face_locations = self._face_recognition.face_locations(rgb_person)
        if not face_locations:
            return None, None, 0.0, False, None
            
        # Get largest face
        top, right, bottom, left = max(face_locations, key=lambda f: (f[2]-f[0]) * (f[1]-f[3]))
        
        # Calculate global face bbox (relative to original frame)
        x1, y1, _, _ = bbox
        face_bbox = (left + x1, top + y1, right + x1, bottom + y1)
        
        # 3. Get encoding
        encodings = self._face_recognition.face_encodings(rgb_person, [(top, right, bottom, left)])
        if not encodings:
            return None, None, 0.0, True, face_bbox
            
        unknown_encoding = encodings[0]
        
        # 4. Compare with known faces
        name = None
        user_id = None
        confidence = 0.0
        
        if self._known_encodings:
            for known_name, known_list in self._known_encodings.items():
                if not known_list:
                    continue
                
                # Check distances
                distances = self._face_recognition.face_distance(known_list, unknown_encoding)
                min_dist = np.min(distances)
                
                if min_dist <= self._tolerance:
                    # Found match
                    score = 1.0 - min_dist
                    if score > confidence:
                        confidence = score
                        name = known_name
                        user_id = self._name_to_id.get(name)
        
        return name, user_id, confidence, True, face_bbox

    def load_from_database(self) -> int:
        """Database-dən bütün üzləri yükləyir."""
        try:
            # Fetch from repository (handles deserialization)
            rows = self._embedding_repo.get_all_face_encodings_with_names()
            
            loaded_count = 0
            self._known_encodings.clear()
            self._name_to_id.clear()
            
            for user_id, name, encoding in rows:
                if name not in self._known_encodings:
                    self._known_encodings[name] = []
                
                self._known_encodings[name].append(encoding)
                self._name_to_id[name] = user_id
                loaded_count += 1
            
            logger.info(f"Loaded {loaded_count} face encodings from database")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load faces from database: {e}")
            return 0
    
    def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        """
        Canlı öyrənmə üçün (əgər lazım olsa).
        DB-yə artıq repository vasitəsilə yazırıq, bura sadəcə cache-i yeniləmək üçündür.
        """
        self._load_library()
        rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        encodings = self.get_encodings(rgb)
        
        if encodings:
            if name not in self._known_encodings:
                self._known_encodings[name] = []
            self._known_encodings[name].append(encodings[0])
            return True
        return False

    @property
    def known_count(self) -> int:
        """Tanınmış şəxs sayı."""
        return len(self._known_encodings)
    
    def get_user_id(self, name: str) -> Optional[int]:
        """Ad üzrə user_id qaytarır."""
        return self._name_to_id.get(name)
