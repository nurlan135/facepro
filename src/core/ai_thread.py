"""
FacePro AI Thread Module
AI processing pipeline üçün QThread.
Motion Detection -> Object Detection -> Face Recognition -> Re-ID -> Gait
"""

import time
from typing import Optional, List, Tuple, Dict

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import crop_person, get_db_path
from src.utils.i18n import tr

# Modular imports
from src.core.detection import Detection, DetectionType, FrameResult
from src.core.motion_detector import MotionDetector
from src.core.object_detector import ObjectDetector
from src.core.face_recognizer import FaceRecognizer
from src.core.reid_engine import get_reid_engine
from src.core.gait_engine import get_gait_engine
from src.core.gait_buffer import GaitBufferManager
from src.core.gait_types import GaitMatch

logger = get_logger()


class AIWorker(QThread):
    """
    AI Processing Pipeline Thread.
    
    Signals:
        frame_processed: Emal olunmuş frame (FrameResult)
        detection_alert: Yeni detection alert-i (Detection, frame)
    """
    
    frame_processed = pyqtSignal(object)  # FrameResult
    detection_alert = pyqtSignal(object, np.ndarray)  # Detection, frame
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._running = False
        self._paused = False
        self._mutex = QMutex()
        self._frame_buffer: Optional[Tuple[np.ndarray, str]] = None

        # AI components
        self._motion_detector = MotionDetector()
        self._object_detector = ObjectDetector()
        self._face_recognizer = FaceRecognizer()
        self._reid_engine = get_reid_engine()
        
        # Gait Recognition components
        self._gait_engine = get_gait_engine()
        self._gait_buffer = GaitBufferManager()
        self._gait_enrollment_buffer = GaitBufferManager()
        
        # Caches
        self._reid_embeddings: List[Tuple[int, int, str, np.ndarray]] = []
        self._gait_embeddings: List[Tuple[int, int, str, np.ndarray]] = []
        self._camera_rois: Dict[str, List[Tuple[float, float]]] = {}
        self._skip_motion_check = False
        
        logger.info("AIWorker initialized")
    
    def run(self):
        """Thread-in əsas döngüsü."""
        self._running = True
        logger.info("AI thread started")
        
        try:
            loaded = self._face_recognizer.load_from_database()
            logger.info(f"Loaded {loaded} known faces from database")
            self._load_reid_embeddings()
            self._load_gait_embeddings()
        except Exception as e:
            logger.error(f"Failed to load faces/embeddings: {e}")
        
        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue
            
            frame_data = None
            with QMutexLocker(self._mutex):
                if self._frame_buffer is not None:
                    frame_data = self._frame_buffer
                    self._frame_buffer = None
            
            if frame_data is None:
                time.sleep(0.01)
                continue
            
            frame, camera_name = frame_data
            
            try:
                result = self._process_frame(frame, camera_name)
                self.frame_processed.emit(result)
                
                for detection in result.detections:
                    if detection.type == DetectionType.PERSON:
                        detection.camera_name = camera_name
                        self.detection_alert.emit(detection, frame)
                
                self._gait_buffer.cleanup_stale()
                self._gait_enrollment_buffer.cleanup_stale()
            except Exception as e:
                logger.error(f"Frame processing error: {e}")
        
        logger.info("AI thread stopped")
    
    def _process_frame(self, frame: np.ndarray, camera_name: str) -> FrameResult:
        """Frame-i emal edir."""
        start_time = time.time()
        result = FrameResult(frame=frame.copy(), camera_name=camera_name)
        
        if not self._skip_motion_check:
            motion = self._motion_detector.detect(frame)
            result.motion_detected = motion
            if not motion:
                result.processing_time_ms = (time.time() - start_time) * 1000
                return result
        else:
            result.motion_detected = True
        
        detections = self._object_detector.detect(frame)
        final_detections = []
        roi_points = self._camera_rois.get(camera_name)
        
        for detection in detections:
            if roi_points and not self._is_inside_roi(self._get_center(detection.bbox, frame.shape), roi_points):
                continue
            if detection.type == DetectionType.PERSON:
                self._process_person(frame, detection)
            final_detections.append(detection)
        
        result.detections = final_detections
        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    def _process_person(self, frame: np.ndarray, detection: Detection):
        """Person detection-ı emal edir."""
        name, user_id, confidence, face_visible, face_bbox = self._face_recognizer.recognize(frame, detection.bbox)
        detection.face_visible = face_visible
        detection.face_bbox = face_bbox
        
        if name:
            detection.label = name
            detection.is_known = True
            detection.confidence = confidence
            detection.identification_method = 'face'
            
            if user_id:
                self._passive_reid_enrollment(frame, detection.bbox, user_id, name)
                if detection.track_id >= 0:
                    self._passive_gait_enrollment(frame, detection.bbox, user_id, detection.track_id)
        else:
            detection.label = "Unknown"
            reid_matched = False
            
            person_crop = crop_person(frame, detection.bbox)
            if person_crop is not None:
                current_embedding = self._reid_engine.extract_embedding(person_crop)
                if current_embedding is not None and self._reid_embeddings:
                    match = self._reid_engine.compare_embeddings(current_embedding, self._reid_embeddings)
                    if match:
                        detection.label = f"{match.user_name} (Re-ID)"
                        detection.is_known = True
                        detection.confidence = match.confidence
                        detection.identification_method = 'reid'
                        reid_matched = True
            
            if not reid_matched and detection.track_id >= 0:
                gait_match = self._try_gait_recognition(frame, detection.bbox, detection.track_id)
                if gait_match:
                    detection.label = f"{gait_match.user_name} (Gait: {gait_match.confidence:.0%})"
                    detection.is_known = True
                    detection.confidence = gait_match.confidence
                    detection.identification_method = 'gait'
    
    def _passive_reid_enrollment(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], user_id: int, name: str):
        """Passive Re-ID enrollment."""
        if np.random.random() >= 0.05:
            return
        person_crop = crop_person(frame, bbox)
        if person_crop is None:
            return
        embedding = self._reid_engine.extract_embedding(person_crop)
        if embedding is not None:
            self._save_reid_embedding(user_id, name, embedding)
    
    def _try_gait_recognition(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], track_id: int) -> Optional[GaitMatch]:
        """Gait recognition cəhdi."""
        try:
            silhouette = self._gait_engine.extract_silhouette(frame, bbox)
            if silhouette is None or silhouette.size == 0:
                return None
            
            is_buffer_full = self._gait_buffer.add_frame(track_id, silhouette)
            if is_buffer_full:
                sequence = self._gait_buffer.get_sequence(track_id)
                if sequence:
                    embedding = self._gait_engine.extract_embedding(sequence)
                    if embedding is not None and self._gait_embeddings:
                        return self._gait_engine.compare_embeddings(embedding, self._gait_embeddings)
            return None
        except Exception as e:
            logger.error(f"Gait recognition failed: {e}")
            return None

    def _passive_gait_enrollment(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], user_id: int, track_id: int):
        """Passive gait enrollment."""
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
                        embedding_id = self._gait_engine.save_embedding(user_id, embedding)
                        if embedding_id:
                            user_name = self._get_user_name(user_id)
                            if user_name:
                                self._gait_embeddings.append((embedding_id, user_id, user_name, embedding))
                                logger.info(f"Passive Gait Enrollment: Saved for {user_name}")
        except Exception as e:
            logger.error(f"Passive gait enrollment failed: {e}")

    def _get_user_name(self, user_id: int) -> Optional[str]:
        """User ID-dən ad tapır."""
        for _, uid, name, _ in self._gait_embeddings:
            if uid == user_id:
                return name
        for name, uid in self._face_recognizer._name_to_id.items():
            if uid == user_id:
                return name
        return None
    
    def _get_center(self, bbox: Tuple[int, int, int, int], shape: Tuple) -> Tuple[float, float]:
        """Bbox mərkəzini normalize edir."""
        x1, y1, x2, y2 = bbox
        h, w = shape[:2]
        return ((x1 + x2) / 2 / w, (y1 + y2) / 2 / h)
    
    def _is_inside_roi(self, point: Tuple[float, float], roi_points: List[Tuple[float, float]]) -> bool:
        """Ray casting algorithm."""
        x, y = point
        inside = False
        j = len(roi_points) - 1
        for i in range(len(roi_points)):
            xi, yi = roi_points[i]
            xj, yj = roi_points[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside
    
    def _load_reid_embeddings(self):
        """Database-dən Re-ID embedding-lərini yükləyir."""
        import sqlite3
        import pickle
        try:
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                SELECT re.id, re.user_id, u.name, re.vector
                FROM reid_embeddings re JOIN users u ON re.user_id = u.id
            """)
            for row in cursor.fetchall():
                emb_id, user_id, user_name, blob = row
                self._reid_embeddings.append((emb_id, user_id, user_name, pickle.loads(blob)))
            conn.close()
            logger.info(f"Loaded {len(self._reid_embeddings)} Re-ID embeddings")
        except Exception as e:
            logger.error(f"Failed to load Re-ID embeddings: {e}")

    def _save_reid_embedding(self, user_id: int, user_name: str, embedding: np.ndarray, confidence: float = 1.0):
        """Re-ID embedding-i saxlayır."""
        try:
            import sqlite3
            import pickle
            self._reid_embeddings.append((0, user_id, user_name, embedding))
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            cursor.execute("INSERT INTO reid_embeddings (user_id, vector, confidence) VALUES (?, ?, ?)",
                          (user_id, pickle.dumps(embedding), confidence))
            conn.commit()
            conn.close()
            logger.info(f"Passive Enrollment: Saved body embedding for {user_name}")
        except Exception as e:
            logger.error(f"Failed to save Re-ID embedding: {e}")

    def _load_gait_embeddings(self):
        """Database-dən Gait embedding-lərini yükləyir."""
        try:
            self._gait_embeddings = self._gait_engine.load_embeddings()
            logger.info(f"Loaded {len(self._gait_embeddings)} Gait embeddings")
        except Exception as e:
            logger.error(f"Failed to load Gait embeddings: {e}")
    
    def process_frame(self, frame: np.ndarray, camera_name: str = "Camera"):
        """Emal üçün frame göndərir (async)."""
        with QMutexLocker(self._mutex):
            self._frame_buffer = (frame.copy(), camera_name)
    
    def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        """Tanınmış üz əlavə edir."""
        return self._face_recognizer.add_known_face(name, face_image)
    
    def stop(self):
        """Thread-i dayandırır."""
        self._running = False
        self.wait(5000)
    
    def pause(self):
        """Thread-i pauzaya alır."""
        with QMutexLocker(self._mutex):
            self._paused = True
    
    def resume(self):
        """Thread-i davam etdirir."""
        with QMutexLocker(self._mutex):
            self._paused = False
    
    def set_camera_roi(self, camera_name: str, points: List[Tuple[float, float]]):
        """Kamera üçün ROI təyin edir."""
        if points and len(points) >= 3:
            self._camera_rois[camera_name] = points
        elif camera_name in self._camera_rois:
            del self._camera_rois[camera_name]


def draw_detections(frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
    """Frame üzərinə detection-ları çəkir."""
    output = frame.copy()
    
    for det in detections:
        if det.type == DetectionType.PERSON:
            if det.is_known:
                if det.identification_method == 'gait':
                    color = (255, 0, 0)  # Mavi - bədən box
                    draw_bbox = det.bbox
                elif det.identification_method == 'reid':
                    color = (0, 255, 255)  # Sarı - bədən box
                    draw_bbox = det.bbox
                else:
                    # Face ilə tanınıb - üz box çək
                    color = (0, 255, 0)  # Yaşıl
                    draw_bbox = det.face_bbox if det.face_bbox else det.bbox
            else:
                color = (0, 0, 255)  # Qırmızı - tanınmayıb
                # Üz görünürsə üz box, yoxsa bədən box
                draw_bbox = det.face_bbox if det.face_bbox else det.bbox
        elif det.type == DetectionType.CAT:
            color = (255, 165, 0)
            draw_bbox = det.bbox
        elif det.type == DetectionType.DOG:
            color = (255, 255, 0)
            draw_bbox = det.bbox
        else:
            color = (128, 128, 128)
            draw_bbox = det.bbox
        
        x1, y1, x2, y2 = draw_bbox
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        label = f"{det.label or det.type.value} ({det.confidence:.0%})"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        # Fon rənginə görə yazı rəngini seç (açıq fon = qara yazı, tünd fon = ağ yazı)
        brightness = (color[0] + color[1] + color[2]) / 3
        text_color = (0, 0, 0) if brightness > 127 else (255, 255, 255)
        cv2.rectangle(output, (x1, y1 - label_h - 10), (x1 + label_w + 4, y1), color, -1)
        cv2.putText(output, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2)
    
    return output
