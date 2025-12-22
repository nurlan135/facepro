"""
FacePro Object Detection Module
YOLO-based Object Detection - Person, Cat, Dog aşkarlayır.
"""

import os
from typing import Optional, List

import numpy as np

from src.utils.logger import get_logger
from src.core.detection import Detection, DetectionType

logger = get_logger()


def get_global_track_id(camera_index: int, local_track_id: int) -> int:
    """
    Multi-camera track ID namespacing.
    
    Problem: Kamera1 track_id=5, Kamera2 track_id=5 -> konflikt
    Həll: Camera-specific prefix
    
    Args:
        camera_index: Kamera indeksi (0, 1, 2, ...)
        local_track_id: YOLO-dan gələn lokal track ID
        
    Returns:
        Qlobal unikal track ID
        
    Examples:
        Kamera 0, track 5 -> 5
        Kamera 1, track 5 -> 100005
        Kamera 2, track 5 -> 200005
    """
    if local_track_id < 0:
        return local_track_id  # Invalid track ID-ləri dəyişmə
    return camera_index * 100000 + local_track_id


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
    
    def detect(self, frame: np.ndarray, use_tracking: bool = True, camera_index: int = 0) -> List[Detection]:
        """
        Frame-də obyektləri aşkarlayır.
        
        Args:
            frame: BGR frame
            use_tracking: YOLO tracking istifadə etmək (track_id üçün)
            camera_index: Kamera indeksi (multi-camera track ID namespacing üçün)
            
        Returns:
            Detection siyahısı
        """
        detections = []
        
        try:
            self._ensure_loaded()
            
            # YOLO inference with tracking for track_id
            if use_tracking:
                results = self._model.track(frame, verbose=False, conf=self._confidence, persist=True)
            else:
                results = self._model(frame, verbose=False, conf=self._confidence)
            
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                
                for i, box in enumerate(boxes):
                    cls_id = int(box.cls[0])
                    
                    # Yalnız icazə verilən class-lar
                    if cls_id not in self.ALLOWED_CLASSES:
                        continue
                    
                    # Bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    # Track ID (if available from tracking)
                    # Apply global namespacing for multi-camera support
                    track_id = -1
                    if use_tracking and box.id is not None:
                        local_track_id = int(box.id[0])
                        track_id = get_global_track_id(camera_index, local_track_id)
                    
                    detection = Detection(
                        type=self.CLASS_NAMES.get(cls_id, DetectionType.UNKNOWN),
                        bbox=(x1, y1, x2, y2),
                        confidence=conf,
                        track_id=track_id
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
        
        return detections
