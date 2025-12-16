"""
FacePro AI Thread Module
AI processing pipeline üçün QThread.
Motion Detection -> Object Detection -> Face Recognition -> Re-ID
"""

import time
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import crop_person, get_db_path
from src.core.reid_engine import get_reid_engine, ReIDEngine

logger = get_logger()


class DetectionType(Enum):
    """Aşkarlama növləri."""
    PERSON = "person"
    CAT = "cat"
    DOG = "dog"
    UNKNOWN = "unknown"


@dataclass
class Detection:
    """Aşkarlama nəticəsi."""
    type: DetectionType
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    label: str = ""  # Face/Re-ID ilə tanınmış ad
    is_known: bool = False
    face_visible: bool = False
    camera_name: str = ""  # Hansı kameradan aşkarlanıb


@dataclass
class FrameResult:
    """Frame emalı nəticəsi."""
    frame: np.ndarray
    detections: List[Detection] = field(default_factory=list)
    motion_detected: bool = False
    processing_time_ms: float = 0.0
    camera_name: str = ""


class MotionDetector:
    """
    Hərəkət aşkarlama modulu.
    CPU qənaəti üçün AI-dən əvvəl işləyir.
    """
    
    def __init__(self, threshold: int = 25, min_area: int = 500):
        """
        Args:
            threshold: Piksel fərqi threshold-u
            min_area: Minimum hərəkət sahəsi (piksel)
        """
        self.threshold = threshold
        self.min_area = min_area
        self._background = None
        self._frame_count = 0
        self._update_interval = 30  # Hər 30 frame-də background yenilə
    
    def detect(self, frame: np.ndarray) -> bool:
        """
        Frame-də hərəkət varmı?
        
        Args:
            frame: BGR frame
            
        Returns:
            Hərəkət aşkarlanıbmı
        """
        # Grayscale və blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # İlk frame -> background olaraq saxla
        if self._background is None:
            self._background = gray.copy()
            return False
        
        # Background yeniləmə
        self._frame_count += 1
        if self._frame_count >= self._update_interval:
            # Yavaş adaptasiya (running average)
            cv2.accumulateWeighted(gray, self._background.astype(np.float32), 0.1)
            self._background = self._background.astype(np.uint8)
            self._frame_count = 0
        
        # Fərq hesabla
        frame_delta = cv2.absdiff(self._background, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate - boşluqları doldur
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Contours tap
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Minimum sahə yoxlaması
        for contour in contours:
            if cv2.contourArea(contour) >= self.min_area:
                return True
        
        return False
    
    def reset(self):
        """Background-u sıfırla."""
        self._background = None
        self._frame_count = 0


class ObjectDetector:
    """
    YOLO-based Object Detection.
    Yalnız Person, Cat, Dog aşkarlayır.
    """
    
    # COCO class IDs
    PERSON_ID = 0
    CAT_ID = 15
    DOG_ID = 16
    
    ALLOWED_CLASSES = {PERSON_ID, CAT_ID, DOG_ID}
    CLASS_NAMES = {
        PERSON_ID: DetectionType.PERSON,
        CAT_ID: DetectionType.CAT,
        DOG_ID: DetectionType.DOG
    }
    
    def __init__(self, model_path: Optional[str] = None, confidence: float = 0.5):
        """
        Args:
            model_path: YOLO model faylı yolu
            confidence: Minimum confidence threshold
        """
        self._model = None
        self._model_path = model_path
        self._confidence = confidence
        logger.info("ObjectDetector created (lazy loading)")
    
    def _ensure_loaded(self):
        """Model-in yükləndiyini təmin edir."""
        if self._model is not None:
            return
        
        try:
            from ultralytics import YOLO
            
            if self._model_path and os.path.exists(self._model_path):
                self._model = YOLO(self._model_path)
            else:
                # Default: models/ qovluğundan oxu
                models_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'models'
                )
                default_path = os.path.join(models_dir, 'yolov8n.pt')
                
                if os.path.exists(default_path):
                    self._model = YOLO(default_path)
                else:
                    # Fallback: ultralytics avtomatik yükləyəcək
                    self._model = YOLO('yolov8n.pt')
            
            logger.info("YOLO model loaded")
            
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            raise
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Frame-də obyektləri aşkarlayır.
        
        Args:
            frame: BGR frame
            
        Returns:
            Detection siyahısı
        """
        detections = []
        
        try:
            self._ensure_loaded()
            
            # YOLO inference
            results = self._model(frame, verbose=False, conf=self._confidence)
            
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                
                for box in boxes:
                    cls_id = int(box.cls[0])
                    
                    # Yalnız icazə verilən class-lar
                    if cls_id not in self.ALLOWED_CLASSES:
                        continue
                    
                    # Bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    detection = Detection(
                        type=self.CLASS_NAMES.get(cls_id, DetectionType.UNKNOWN),
                        bbox=(x1, y1, x2, y2),
                        confidence=conf
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
        
        return detections


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
            # NOTE: New faces added at runtime won't have ID until reload or separate ID handling.
            # But for Re-ID logic we really need the ID. 
            # For now, we only support Passive Enrollment for faces loaded from DB (which have IDs).
            
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
        
        # Frame queue (sadə buffer)
        self._frame_buffer: Optional[Tuple[np.ndarray, str]] = None
        
        # AI components
        self._motion_detector = MotionDetector()
        self._object_detector = ObjectDetector()
        self._object_detector = ObjectDetector()
        self._face_recognizer = FaceRecognizer()
        self._reid_engine = get_reid_engine()
        
        # Re-ID Cache: {user_id: [embedding]}
        # Re-ID Cache: {user_id: [embedding]}
        self._reid_embeddings: List[Tuple[int, int, str, np.ndarray]] = []  # (emb_id, user_id, user_name, embedding)
        
        # Camera ROIs: {camera_name: [(x, y), ...]} normalized
        self._camera_rois: Dict[str, List[Tuple[float, float]]] = {}
        
        # Settings
        self._skip_motion_check = False  # Debug üçün
        
        logger.info("AIWorker initialized")
    
    def run(self):
        """Thread-in əsas döngüsü."""
        self._running = True
        logger.info("AI thread started")
        
        # Database-dən tanınmış üzləri yüklə
        try:
            loaded = self._face_recognizer.load_from_database()
            logger.info(f"Loaded {loaded} known faces from database")
            
            # Load Re-ID embeddings
            self._load_reid_embeddings()
            
        except Exception as e:
            logger.error(f"Failed to load faces/embeddings: {e}")
        
        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue
            
            # Frame buffer-dən oxu
            frame_data = None
            with QMutexLocker(self._mutex):
                if self._frame_buffer is not None:
                    frame_data = self._frame_buffer
                    self._frame_buffer = None
            
            if frame_data is None:
                time.sleep(0.01)
                continue
            
            frame, camera_name = frame_data
            
            # Process
            try:
                result = self._process_frame(frame, camera_name)
                self.frame_processed.emit(result)
                
                # Alert-lər
                for detection in result.detections:
                    if detection.type == DetectionType.PERSON:
                        detection.camera_name = camera_name
                        self.detection_alert.emit(detection, frame)
                        
            except Exception as e:
                logger.error(f"Frame processing error: {e}")
        
        logger.info("AI thread stopped")
    
    def _process_frame(self, frame: np.ndarray, camera_name: str) -> FrameResult:
        """
        Frame-i emal edir.
        
        Pipeline:
        1. Motion Detection (gatekeeper)
        2. Object Detection (YOLO)
        3. Face Recognition (əgər person varsa)
        4. Re-ID (əgər üz görünmürsə)
        """
        start_time = time.time()
        
        result = FrameResult(
            frame=frame.copy(),
            camera_name=camera_name
        )
        
        # 1. Motion Detection
        if not self._skip_motion_check:
            motion = self._motion_detector.detect(frame)
            result.motion_detected = motion
            
            if not motion:
                # Hərəkət yoxdur, AI skip
                result.processing_time_ms = (time.time() - start_time) * 1000
                return result
        else:
            result.motion_detected = True
        
        # 2. Object Detection
        detections = self._object_detector.detect(frame)
        
        # 3. Face Recognition (hər person üçün)
        # Filter by ROI if exists
        final_detections = []
        roi_points = self._camera_rois.get(camera_name)
        
        for detection in detections:
            # Check ROI
            if roi_points:
                x1, y1, x2, y2 = detection.bbox
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Normalize center
                h, w = frame.shape[:2]
                norm_center = (center_x / w, center_y / h)
                
                if not self._is_inside_roi(norm_center, roi_points):
                    continue

            if detection.type == DetectionType.PERSON:
                name, user_id, confidence, face_visible = self._face_recognizer.recognize(frame, detection.bbox)
                
                detection.face_visible = face_visible
                
                if name:
                    detection.label = name
                    detection.is_known = True
                    detection.confidence = confidence
                    
                    # PASSIVE ENROLLMENT:
                    # Əgər üz tanınıbsa, bədən xüsusiyyətlərini öyrən və bazaya yaz.
                    # Bu, gələcəkdə üz görünməyəndə (arxadan) tanımaq üçün lazımdır.
                    if user_id:
                        person_crop = crop_person(frame, detection.bbox)
                        if person_crop is not None:
                            embedding = self._reid_engine.extract_embedding(person_crop)
                            if embedding is not None:
                                # Burada bir optimizasiya edə bilərik:
                                # Hər frame-də yazmaq əvəzinə, yalnız əgər bu bucaqdan/geyimdən yoxdursa yazaq.
                                # MVP üçün sadəlik xatirinə yazırıq (lakin 30 fps-də çox ola bilər).
                                # HƏLL: Yalnız 1% ehtimalla yazaq və ya in-memory yoxlayaq.
                                # Sadə random sampling (hər 100 frame-dən bir)
                                if np.random.random() < 0.05:  # 5% ehtimal
                                    self._save_reid_embedding(user_id, name, embedding)
                else:
                    detection.label = "Unknown"
                    
                    # Re-ID Attempt (if face not found/recognized)
                    person_crop = crop_person(frame, detection.bbox)
                    if person_crop is not None:
                        current_embedding = self._reid_engine.extract_embedding(person_crop)
                        
                        if current_embedding is not None and self._reid_embeddings:
                            # Compare with stored embeddings
                            match = self._reid_engine.compare_embeddings(current_embedding, self._reid_embeddings)
                            
                            if match:
                                detection.label = f"{match.user_name} (Re-ID)"
                                detection.is_known = True
                                detection.confidence = match.confidence
                                logger.debug(f"Re-ID matched: {match.user_name} ({match.confidence:.2%})")
            
            final_detections.append(detection)
        
        result.detections = final_detections
        result.processing_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def process_frame(self, frame: np.ndarray, camera_name: str = "Camera"):
        """
        Emal üçün frame göndərir (async).
        
        Args:
            frame: BGR frame
            camera_name: Kamera adı
        """
        with QMutexLocker(self._mutex):
            self._frame_buffer = (frame.copy(), camera_name)
    
    def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        """Tanınmış üz əlavə edir."""
        return self._face_recognizer.add_known_face(name, face_image)
    
    def stop(self):
        """Thread-i dayandırır."""
        self._running = False
        self.wait(5000)
    
    def set_camera_roi(self, camera_name: str, points: List[Tuple[float, float]]):
        """Kamera üçün ROI təyin edir."""
        if points and len(points) >= 3:
            self._camera_rois[camera_name] = points
            logger.info(f"ROI set for {camera_name}: {len(points)} points")
        else:
            if camera_name in self._camera_rois:
                del self._camera_rois[camera_name]
    
    def _is_inside_roi(self, point: Tuple[float, float], roi_points: List[Tuple[float, float]]) -> bool:
        """Nöqtənin ROI daxilində olub-olmadığını yoxlayır."""
        # Ray casting algorithm
        x, y = point
        inside = False
        j = len(roi_points) - 1
        
        for i in range(len(roi_points)):
            xi, yi = roi_points[i]
            xj, yj = roi_points[j]
            
            intersect = ((yi > y) != (yj > y)) and \
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
            
            if intersect:
                inside = not inside
            j = i
            
        return inside
        
    def pause(self):
        """Thread-i pauzaya alır."""
        with QMutexLocker(self._mutex):
            self._paused = True
    
    def resume(self):
        """Thread-i davam etdirir."""
        with QMutexLocker(self._mutex):
            self._paused = False

    def _load_reid_embeddings(self):
        """Database-dən Re-ID embedding-lərini yükləyir."""
        import sqlite3
        import pickle
        
        db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Using 'vector' column as per schema
            cursor.execute("""
                SELECT re.id, re.user_id, u.name, re.vector
                FROM reid_embeddings re
                JOIN users u ON re.user_id = u.id
            """)
            
            for row in cursor.fetchall():
                emb_id, user_id, user_name, blob = row
                embedding = pickle.loads(blob)
                self._reid_embeddings.append((emb_id, user_id, user_name, embedding))
                
            conn.close()
            logger.info(f"Loaded {len(self._reid_embeddings)} Re-ID embeddings")
            
        except Exception as e:
            logger.error(f"Failed to load Re-ID embeddings: {e}")

    def _save_reid_embedding(self, user_id: int, user_name: str, embedding: np.ndarray, confidence: float = 1.0):
        """Re-ID embedding-i database-ə və yaddaşa yazır."""
        try:
            import sqlite3
            import pickle
            
            # 1. Update In-Memory
            # Fake ID for memory (DB-dən oxuyanda real ID gələcək)
            # Bizə əslində sadəcə müqayisə üçün lazımdır
            self._reid_embeddings.append((0, user_id, user_name, embedding))
            
            # 2. Write to DB
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            blob = pickle.dumps(embedding)
            
            cursor.execute("""
                INSERT INTO reid_embeddings (user_id, vector, confidence)
                VALUES (?, ?, ?)
            """, (user_id, blob, confidence))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Passive Enrollment: Saved body embedding for {user_name}")
            
        except Exception as e:
            logger.error(f"Failed to save Re-ID embedding: {e}")


def draw_detections(frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
    """
    Frame üzərinə detection-ları çəkir.
    
    Args:
        frame: Orijinal frame
        detections: Detection siyahısı
        
    Returns:
        Annotated frame
    """
    output = frame.copy()
    
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        
        # Rəng seçimi
        if det.type == DetectionType.PERSON:
            if det.is_known:
                color = (0, 255, 0)  # Yaşıl - tanınmış
            else:
                color = (0, 0, 255)  # Qırmızı - yad
        elif det.type == DetectionType.CAT:
            color = (255, 165, 0)  # Narıncı
        elif det.type == DetectionType.DOG:
            color = (255, 255, 0)  # Sarı
        else:
            color = (128, 128, 128)  # Boz
        
        # Bounding box
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        
        # Label
        label = f"{det.label or det.type.value} ({det.confidence:.0%})"
        
        # Label background
        (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(output, (x1, y1 - label_h - 10), (x1 + label_w, y1), color, -1)
        
        # Label text
        cv2.putText(output, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return output


if __name__ == "__main__":
    # Test
    print("Testing AI components...")
    
    # Motion detector test
    motion = MotionDetector()
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    print(f"Motion (frame 1): {motion.detect(test_frame)}")
    print(f"Motion (frame 2): {motion.detect(test_frame)}")
    
    # Modified frame
    test_frame[200:300, 300:400] = 255
    print(f"Motion (modified): {motion.detect(test_frame)}")
    
    print("\nAI components test complete")
