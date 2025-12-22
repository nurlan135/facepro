"""
FacePro Face Recognition Module
-------------------------------
Supports both dlib/face_recognition and InsightFace (ONNX) backends.
InsightFace is the default and recommended backend (~6x faster than dlib).

Backend Selection:
    - 'insightface' (default): Fast, ONNX-based, 512d embeddings
    - 'dlib': Legacy support, 128d embeddings

Note: Embeddings from different backends are NOT compatible!
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
    InsightFace (default) və ya dlib backend-ini istifadə edir.
    
    Supports Dependency Injection for testing:
        recognizer = FaceRecognizer(embedding_repo=mock_repo)
    """
    
    # Backend types
    BACKEND_INSIGHTFACE = 'insightface'
    BACKEND_DLIB = 'dlib'
    
    def __init__(
        self, 
        tolerance: float = 0.4, 
        backend: str = 'insightface',
        embedding_repo: Optional[EmbeddingRepository] = None
    ):
        """
        Args:
            tolerance: Face matching threshold
                       - InsightFace: 0.4 (cosine similarity, higher = stricter)
                       - Dlib: 0.6 (distance, lower = stricter)
            backend: 'insightface' (default) or 'dlib'
            embedding_repo: Optional repository for DI (testing)
        """
        self._backend_type = backend
        self._tolerance = tolerance
        self._known_encodings: Dict[str, List[np.ndarray]] = {}  # {name: [encodings]}
        self._name_to_id: Dict[str, int] = {}  # {name: user_id}
        self._embedding_repo = embedding_repo or EmbeddingRepository()
        
        # Backend instances (lazy loaded)
        self._insightface_adapter = None
        self._dlib_module = None
        
        logger.info(f"FaceRecognizer created (backend={backend}, lazy loading)")

    def _load_insightface(self):
        """Lazy load InsightFace adapter."""
        if self._insightface_adapter is None:
            try:
                from src.core.detectors.insightface_adapter import InsightFaceAdapter
                self._insightface_adapter = InsightFaceAdapter(provider='auto')
                logger.info("InsightFace backend loaded")
            except Exception as e:
                logger.error(f"Failed to load InsightFace: {e}")
                raise

    def _load_dlib(self):
        """Lazy load dlib/face_recognition library."""
        if self._dlib_module is None:
            try:
                import face_recognition
                self._dlib_module = face_recognition
                logger.info("Dlib/face_recognition backend loaded")
            except ImportError:
                logger.error("face_recognition library not found!")
                raise

    def get_encodings(self, rgb_image: np.ndarray) -> List[np.ndarray]:
        """
        Şəkildən üz vektorlarını çıxarır.
        
        Args:
            rgb_image: RGB formatında şəkil (InsightFace üçün BGR lazımdır)
            
        Returns:
            List of face embeddings
        """
        if self._backend_type == self.BACKEND_INSIGHTFACE:
            self._load_insightface()
            # InsightFace BGR istəyir
            bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
            return self._insightface_adapter.get_all_embeddings(bgr_image)
        else:
            self._load_dlib()
            face_locations = self._dlib_module.face_locations(rgb_image)
            if not face_locations:
                return []
            return self._dlib_module.face_encodings(rgb_image, face_locations)

    def recognize(
        self, 
        frame: np.ndarray, 
        bbox: Tuple[int, int, int, int]
    ) -> Tuple[Optional[str], Optional[int], float, bool, Optional[Tuple]]:
        """
        Person bbox daxilində üz tanımağa çalışır.
        
        Returns:
            (name, user_id, confidence, face_visible, face_bbox)
        """
        # 1. Person crop
        person_img = crop_person(frame, bbox)
        if person_img is None or person_img.size == 0:
            return None, None, 0.0, False, None
        
        if self._backend_type == self.BACKEND_INSIGHTFACE:
            return self._recognize_insightface(person_img, bbox)
        else:
            return self._recognize_dlib(person_img, bbox)

    def _recognize_insightface(
        self, 
        person_img: np.ndarray, 
        original_bbox: Tuple[int, int, int, int]
    ) -> Tuple[Optional[str], Optional[int], float, bool, Optional[Tuple]]:
        """InsightFace backend ilə tanıma."""
        self._load_insightface()
        
        # Detect faces in person crop
        faces = self._insightface_adapter.detect_faces(person_img)
        
        if not faces:
            return None, None, 0.0, False, None
        
        # Get largest face
        largest_face = max(faces, key=lambda f: 
            (f['bbox'][2] - f['bbox'][0]) * (f['bbox'][3] - f['bbox'][1])
        )
        
        # Calculate global face bbox (relative to original frame)
        x1, y1, _, _ = original_bbox
        local_bbox = largest_face['bbox']
        face_bbox = (
            local_bbox[0] + x1,
            local_bbox[1] + y1,
            local_bbox[2] + x1,
            local_bbox[3] + y1
        )
        
        unknown_embedding = largest_face['embedding']
        
        # Compare with known faces
        name = None
        user_id = None
        confidence = 0.0
        
        if self._known_encodings:
            matched_name, score = self._insightface_adapter.find_best_match(
                unknown_embedding,
                self._known_encodings,
                threshold=self._tolerance
            )
            
            if matched_name:
                name = matched_name
                user_id = self._name_to_id.get(name)
                confidence = score
        
        return name, user_id, confidence, True, face_bbox

    def _recognize_dlib(
        self, 
        person_img: np.ndarray, 
        original_bbox: Tuple[int, int, int, int]
    ) -> Tuple[Optional[str], Optional[int], float, bool, Optional[Tuple]]:
        """Dlib backend ilə tanıma (legacy)."""
        self._load_dlib()
        
        rgb_person = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGB)
        
        # Detect face in crop
        face_locations = self._dlib_module.face_locations(rgb_person)
        if not face_locations:
            return None, None, 0.0, False, None
        
        # Get largest face
        top, right, bottom, left = max(
            face_locations, 
            key=lambda f: (f[2]-f[0]) * (f[1]-f[3])
        )
        
        # Calculate global face bbox
        x1, y1, _, _ = original_bbox
        face_bbox = (left + x1, top + y1, right + x1, bottom + y1)
        
        # Get encoding
        encodings = self._dlib_module.face_encodings(
            rgb_person, 
            [(top, right, bottom, left)]
        )
        if not encodings:
            return None, None, 0.0, True, face_bbox
        
        unknown_encoding = encodings[0]
        
        # Compare with known faces
        name = None
        user_id = None
        confidence = 0.0
        
        if self._known_encodings:
            for known_name, known_list in self._known_encodings.items():
                if not known_list:
                    continue
                
                distances = self._dlib_module.face_distance(known_list, unknown_encoding)
                min_dist = np.min(distances)
                
                # Dlib: lower distance = better match
                # tolerance is typically 0.6 for dlib
                if min_dist <= self._tolerance:
                    score = 1.0 - min_dist
                    if score > confidence:
                        confidence = score
                        name = known_name
                        user_id = self._name_to_id.get(name)
        
        return name, user_id, confidence, True, face_bbox

    def load_from_database(self) -> int:
        """
        Database-dən bütün üzləri yükləyir.
        
        NOTE: Backend dəyişdirilərsə, köhnə embedding-lər işləməyəcək!
        """
        try:
            rows = self._embedding_repo.get_all_face_encodings_with_names()
            
            loaded_count = 0
            self._known_encodings.clear()
            self._name_to_id.clear()
            
            expected_dim = 512 if self._backend_type == self.BACKEND_INSIGHTFACE else 128
            
            for user_id, name, encoding in rows:
                # Dimension check
                if encoding is not None and len(encoding) != expected_dim:
                    logger.warning(
                        f"Skipping face for '{name}': dimension mismatch "
                        f"(got {len(encoding)}, expected {expected_dim})"
                    )
                    continue
                
                if name not in self._known_encodings:
                    self._known_encodings[name] = []
                
                self._known_encodings[name].append(encoding)
                self._name_to_id[name] = user_id
                loaded_count += 1
            
            logger.info(
                f"Loaded {loaded_count} face encodings from database "
                f"(backend={self._backend_type})"
            )
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load faces from database: {e}")
            return 0
    
    def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        """
        Canlı öyrənmə üçün.
        
        Args:
            name: Şəxsin adı
            face_image: BGR formatında üz şəkli
            
        Returns:
            True if successful
        """
        if self._backend_type == self.BACKEND_INSIGHTFACE:
            self._load_insightface()
            embedding = self._insightface_adapter.get_embedding(face_image)
            if embedding is not None:
                if name not in self._known_encodings:
                    self._known_encodings[name] = []
                self._known_encodings[name].append(embedding)
                return True
            return False
        else:
            self._load_dlib()
            rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            encodings = self.get_encodings(rgb)
            if encodings:
                if name not in self._known_encodings:
                    self._known_encodings[name] = []
                self._known_encodings[name].append(encodings[0])
                return True
            return False

    def get_embedding_for_image(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Şəkildən embedding çıxarır (enrollment üçün).
        
        Args:
            face_image: BGR formatında şəkil
            
        Returns:
            Embedding array or None
        """
        if self._backend_type == self.BACKEND_INSIGHTFACE:
            self._load_insightface()
            return self._insightface_adapter.get_embedding(face_image)
        else:
            self._load_dlib()
            rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            encodings = self.get_encodings(rgb)
            return encodings[0] if encodings else None

    @property
    def known_count(self) -> int:
        """Tanınmış şəxs sayı."""
        return len(self._known_encodings)
    
    def get_user_id(self, name: str) -> Optional[int]:
        """Ad üzrə user_id qaytarır."""
        return self._name_to_id.get(name)

    @property
    def backend(self) -> str:
        """Aktiv backend adı."""
        return self._backend_type
    
    @property
    def embedding_dim(self) -> int:
        """Embedding dimensiyası."""
        return 512 if self._backend_type == self.BACKEND_INSIGHTFACE else 128
