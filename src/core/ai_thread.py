"""
FacePro AI Thread Module
AI processing pipeline - Orchestrator using Services.
Motion Detection -> Object Detection -> Recognition Service
"""

import time
from typing import Optional, List, Tuple, Dict

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

from src.utils.logger import get_logger

# Modular imports
from src.core.detection import Detection, DetectionType, FrameResult
from src.core.storage_worker import StorageWorker

# Services
from src.core.services.recognition_service import RecognitionService
from src.core.services.detection_service import DetectionService

logger = get_logger()


class AIWorker(QThread):
    """
    AI Processing Pipeline Thread (Orchestrator).
    Delegates complex logic to dedicated services.
    
    Signals:
        frame_processed: Processed frame result (FrameResult)
        detection_alert: New detection alert (Detection, frame)
        event_saved_signal: Relay for storage worker
    """
    
    frame_processed = pyqtSignal(object)  # FrameResult
    detection_alert = pyqtSignal(object, np.ndarray)  # Detection, frame

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._running = False
        self._paused = False
        self._mutex = QMutex()
        self._frame_buffer: Optional[Tuple[np.ndarray, str]] = None

        # Async Workers
        self._storage_worker = StorageWorker()
        # event_saved signal is not used by AIWorker's consumers, so we don't need to relay it.
        
        # Services
        self._detection_service = DetectionService()
        self._recognition_service = RecognitionService(self._storage_worker)
        
        logger.info("AIWorker (Orchestrator) initialized")
    
    def run(self):
        """Main Thread Loop."""
        self._running = True
        logger.info("AI thread started")
        
        # Start Async Workers
        self._storage_worker.start()

        # Initialize Services
        self._recognition_service.load_data()
        
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
                
                # Check for High-Confidence Person Alerts
                for detection in result.detections:
                    if detection.type == DetectionType.PERSON:
                        detection.camera_name = camera_name
                        self.detection_alert.emit(detection, frame)
                        # We do NOT save event here to avoid duplicates and spam.
                        # MainWindow handles event filtering (cooldown) and saving.
                
                # Periodic Cleanup
                self._recognition_service.cleanup_buffers()
                
            except Exception as e:
                logger.error(f"Frame processing error: {e}")
        
        self._storage_worker.stop()
        logger.info("AI thread stopped")
    
    def _process_frame(self, frame: np.ndarray, camera_name: str) -> FrameResult:
        """Single Frame Processing Pipeline."""
        start_time = time.time()
        
        # PERFORMANCE: Don't copy frame immediately - only copy if needed for detection display
        result = FrameResult(frame=None, camera_name=camera_name)
        
        # 1. Detection Service (Motion + Objects + ROI)
        motion_detected, detections = self._detection_service.detect(frame, camera_name)
        result.motion_detected = motion_detected
        
        if not motion_detected:
            result.processing_time_ms = (time.time() - start_time) * 1000
            return result
        
        # 2. Recognition Service (Face + ReID + Gait)
        for detection in detections:
            if detection.type == DetectionType.PERSON:
                self._recognition_service.process_identity(frame, detection)
        
        result.detections = detections
        
        # PERFORMANCE: Only copy frame if there are detections to display
        # This saves ~6MB per frame (1080p) when no detections
        if detections:
            result.frame = frame.copy()
        
        result.processing_time_ms = (time.time() - start_time) * 1000
        return result
    
    # ================= Helper Methods =================

    def add_known_face(self, name: str, face_image: np.ndarray) -> bool:
        """Forward to service."""
        return self._recognition_service.add_known_face(name, face_image)
    
    def process_frame(self, frame: np.ndarray, camera_name: str = "Camera"):
        """Queue frame for AI processing. Thread-safe - frame is copied."""
        with QMutexLocker(self._mutex):
            # NOTE: Copy is required here for thread safety - frame may be modified
            # by camera thread while AI thread processes it
            self._frame_buffer = (frame.copy(), camera_name)

    def stop(self):
        self._running = False
        self.wait(5000)
    
    def pause(self):
        with QMutexLocker(self._mutex):
            self._paused = True
    
    def resume(self):
        with QMutexLocker(self._mutex):
            self._paused = False
    
    def set_camera_roi(self, camera_name: str, points: List[Tuple[float, float]]):
        self._detection_service.set_roi(camera_name, points)

# ================= Drawing Helper (Kept here for UI usage compatibility) =================

def draw_detections(frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
    output = frame.copy()
    
    for det in detections:
        draw_bbox = det.bbox
        text_color = (255, 255, 255)
        
        if det.type == DetectionType.PERSON:
            draw_bbox = det.face_bbox if (det.face_visible and det.face_bbox) else det.bbox
            if det.is_known:
                if det.identification_method == 'gait':
                    color = (255, 0, 0)      # Blue (Gait)
                    draw_bbox = det.bbox     # Gait is body-based
                elif det.identification_method == 'reid':
                    color = (0, 255, 255)    # Yellow (Re-ID)
                    draw_bbox = det.bbox     # Re-ID is body-based
                else: 
                    color = (0, 255, 0)      # Green (Face)
            else:
                color = (0, 0, 255)          # Red (Unknown)
        elif det.type == DetectionType.CAT:
            color = (255, 165, 0)            # Orange
        elif det.type == DetectionType.DOG:
            color = (255, 255, 0)            # Cyan
        else:
            color = (128, 128, 128)          # Gray
        
        x1, y1, x2, y2 = draw_bbox
        cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
        
        label = f"{det.label or det.type.value} ({det.confidence:.0%})"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        
        cv2.rectangle(output, (x1, y1 - label_h - 10), (x1 + label_w + 4, y1), color, -1)
        
        # Adaptive text color
        brightness = (color[0] + color[1] + color[2]) / 3
        text_color = (0, 0, 0) if brightness > 127 else (255, 255, 255)
        
        cv2.putText(output, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2)
    
    return output
