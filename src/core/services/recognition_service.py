
import numpy as np
import time
from typing import List, Tuple, Optional, Dict

from src.utils.logger import get_logger
from src.utils.helpers import crop_person

from src.core.detection import Detection
from src.core.face_recognizer import FaceRecognizer
from src.core.reid_engine import get_reid_engine
from src.core.gait_engine import get_gait_engine
from src.core.gait_buffer import GaitBufferManager
from src.core.database.repositories.embedding_repository import EmbeddingRepository
from src.core.services.matching_service import MatchingService

logger = get_logger()

class RecognitionService:
    """
    Handles all identity verification logic:
    - Face Recognition
    - Person Re-Identification (Body)
    - Gait Recognition
    - Passive Enrollment dispatch
    """
    
    # Re-ID Passive Enrollment Constants
    REID_SAMPLE_INTERVAL = 2.0       # saniyə - sampling intervalı
    REID_MIN_SAMPLES = 10            # minimum sample sayı
    REID_MAX_SAMPLES = 50            # maksimum sample sayı
    
    def __init__(self, storage_worker):
        self._storage_worker = storage_worker
        
        # Core Engines
        self._face_recognizer = FaceRecognizer()
        self._reid_engine = get_reid_engine()
        self._gait_engine = get_gait_engine()
        
        # Vector Matching Service
        self._matching_service = MatchingService()
        
        # Buffers
        self._gait_buffer = GaitBufferManager()
        self._gait_enrollment_buffer = GaitBufferManager()
        
        # Repository
        self._embedding_repo = EmbeddingRepository()
        
        # Per-user Re-ID sampling tracking
        self._user_reid_samples: Dict[int, int] = {}      # user_id -> sample count
        self._user_last_sample: Dict[int, float] = {}     # user_id -> timestamp

        logger.info("RecognitionService initialized")

    def load_data(self):
        """Loads all known faces and embeddings into memory."""
        try:
            # 1. Face Data (Managed by Dlib wrapper for now)
            loaded_faces = self._face_recognizer.load_from_database()
            
            # 2. Re-ID Data
            reid_data = self._embedding_repo.get_reid_embeddings_with_names()
            self._matching_service.load_reid_data(reid_data)
            
            # 3. Gait Data
            gait_data = self._embedding_repo.get_gait_embeddings_with_names()
            self._matching_service.load_gait_data(gait_data)
            
            logger.info(f"RecognitionService ready. Faces: {loaded_faces}")
        except Exception as e:
            logger.error(f"Failed to load recognition data: {e}")

    def cleanup_buffers(self):
        """Clean stale gait buffers."""
        self._gait_buffer.cleanup_stale()
        self._gait_enrollment_buffer.cleanup_stale()

    def process_identity(self, frame: np.ndarray, detection: Detection):
        """
        Run the full identification pipeline on a person detection.
        Updates the 'detection' object in-place.
        """
        # 1. Face Recognition
        name, user_id, confidence, face_visible, face_bbox = self._face_recognizer.recognize(frame, detection.bbox)
        detection.face_visible = face_visible
        detection.face_bbox = face_bbox
        
        if name:
            # IDENTITY FOUND BY FACE
            detection.label = name
            detection.is_known = True
            detection.confidence = confidence
            detection.identification_method = 'face'
            
            # Passive Enrollment
            if user_id:
                self._passive_enrollment(frame, detection, user_id, name)
            
        else:
            # 2. Fallback to Re-ID
            detection.label = "Unknown"
            reid_matched = False
            
            person_crop = crop_person(frame, detection.bbox)
            if person_crop is not None:
                current_embedding = self._reid_engine.extract_embedding(person_crop)
                if current_embedding is not None:
                    # Use Matching Service
                    match = self._matching_service.match_reid(current_embedding)
                    
                    if match:
                        detection.label = f"{match.user_name} (Re-ID)"
                        detection.is_known = True
                        detection.confidence = match.confidence
                        detection.identification_method = 'reid'
                        reid_matched = True
            
            # 3. Fallback to Gait (if tracking is stable)
            if not reid_matched and detection.track_id >= 0:
                gait_match = self._try_gait_recognition(frame, detection.bbox, detection.track_id)
                if gait_match:
                    detection.label = f"{gait_match.user_name} (Gait: {gait_match.confidence:.0%})"
                    detection.is_known = True
                    detection.confidence = gait_match.confidence
                    detection.identification_method = 'gait'

    def _should_sample_reid(self, user_id: int) -> bool:
        """
        İstifadəçi üçün Re-ID sample götürülməli olub-olmadığını müəyyən edir.
        
        Time-based sampling:
        - Hər REID_SAMPLE_INTERVAL saniyədə bir sample götür
        - REID_MAX_SAMPLES-ə çatdıqda dayandır
        
        Args:
            user_id: İstifadəçi ID-si
            
        Returns:
            Sample götürülməli olub-olmadığı
        """
        now = time.time()
        
        # Max limitə çatdıqda sampling dayandır
        current_count = self._user_reid_samples.get(user_id, 0)
        if current_count >= self.REID_MAX_SAMPLES:
            return False
        
        # Time-based sampling
        last_sample = self._user_last_sample.get(user_id, 0)
        if now - last_sample < self.REID_SAMPLE_INTERVAL:
            return False
        
        return True

    def _passive_enrollment(self, frame: np.ndarray, detection: Detection, user_id: int, name: str):
        """Handles passive learning of Body and Gait features."""
        # Body Re-ID Enrollment (Time-based sampling)
        if self._should_sample_reid(user_id):
            person_crop = crop_person(frame, detection.bbox)
            if person_crop is not None:
                embedding = self._reid_engine.extract_embedding(person_crop)
                if embedding is not None:
                    # Async Save
                    self._storage_worker.add_reid_task(user_id, embedding)
                    # Optimistic RAM Update via Matching Service
                    self._matching_service.add_reid_vector(user_id, name, embedding)
                    
                    # Update counters
                    self._user_reid_samples[user_id] = self._user_reid_samples.get(user_id, 0) + 1
                    self._user_last_sample[user_id] = time.time()
                    
                    logger.info(f"Re-ID sample {self._user_reid_samples[user_id]}/{self.REID_MAX_SAMPLES} for {name}")

        # Gait Enrollment (Sequence based)
        if detection.track_id >= 0:
             self._passive_gait_enrollment(frame, detection.bbox, user_id, detection.track_id, name)

    def _passive_gait_enrollment(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], user_id: int, track_id: int, name: str):
        try:
            silhouette = self._gait_engine.extract_silhouette(frame, bbox)
            if silhouette is None or silhouette.size == 0:
                return
            
            enrollment_key = user_id * 10000 + (track_id % 10000)
            is_buffer_full = self._gait_enrollment_buffer.add_frame(enrollment_key, silhouette)
            
            if is_buffer_full:
                sequence = self._gait_enrollment_buffer.get_sequence(enrollment_key)
                if sequence:
                    embedding = self._gait_engine.extract_embedding(sequence)
                    if embedding is not None:
                        # Async Save
                        self._storage_worker.add_gait_task(user_id, embedding)
                        # Optimistic RAM Update
                        self._matching_service.add_gait_vector(user_id, name, embedding)
                        logger.info(f"Passive Gait Enrollment: Captured sequence for {name}")
        except Exception as e:
            logger.error(f"Passive gait enrollment error: {e}")

    def _try_gait_recognition(self, frame, bbox, track_id):
        try:
            silhouette = self._gait_engine.extract_silhouette(frame, bbox)
            if silhouette is None or silhouette.size == 0:
                return None
            
            is_buffer_full = self._gait_buffer.add_frame(track_id, silhouette)
            if is_buffer_full:
                sequence = self._gait_buffer.get_sequence(track_id)
                if sequence:
                    embedding = self._gait_engine.extract_embedding(sequence)
                    if embedding is not None:
                        # Use Matching Service
                        return self._matching_service.match_gait(embedding)
            return None
        except Exception as e:
            logger.error(f"Gait recognition error: {e}")
            return None

    def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        return self._face_recognizer.add_known_face(name, face_image)
