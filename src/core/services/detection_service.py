
import cv2
import numpy as np
import time
from typing import List, Tuple, Optional, Dict

from src.utils.logger import get_logger
from src.core.detection import Detection, DetectionType
from src.core.motion_detector import MotionDetector
from src.core.object_detector import ObjectDetector

logger = get_logger()

class DetectionService:
    """
    Handles all detection logic:
    - Motion Detection
    - Object Detection (YOLO)
    - ROI (Region of Interest) filtering
    """
    def __init__(self):
        self._motion_detector = MotionDetector()
        self._object_detector = ObjectDetector()
        self._camera_rois: Dict[str, List[Tuple[float, float]]] = {}
        self._skip_motion_check = False
        
        logger.info("DetectionService initialized")

    def detect(self, frame: np.ndarray, camera_name: str) -> Tuple[bool, List[Detection]]:
        """
        Runs the detection pipeline.
        Returns: (motion_detected, list_of_detections)
        """
        # 1. Motion Detection
        motion_detected = True
        if not self._skip_motion_check:
            motion_detected = self._motion_detector.detect(frame)
            if not motion_detected:
                return False, []
        
        # 2. Object Detection
        raw_detections = self._object_detector.detect(frame)
        
        # 3. ROI Filtering
        final_detections = []
        roi_points = self._camera_rois.get(camera_name)
        
        for detection in raw_detections:
            if roi_points:
                center = self._get_center(detection.bbox, frame.shape)
                if not self._is_inside_roi(center, roi_points):
                    continue
            final_detections.append(detection)
            
        return True, final_detections

    def set_roi(self, camera_name: str, points: List[Tuple[float, float]]):
        if points and len(points) >= 3:
            self._camera_rois[camera_name] = points
        elif camera_name in self._camera_rois:
            del self._camera_rois[camera_name]

    def _get_center(self, bbox: Tuple[int, int, int, int], shape: Tuple) -> Tuple[float, float]:
        x1, y1, x2, y2 = bbox
        h, w = shape[:2]
        return ((x1 + x2) / 2 / w, (y1 + y2) / 2 / h)
    
    def _is_inside_roi(self, point: Tuple[float, float], roi_points: List[Tuple[float, float]]) -> bool:
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
