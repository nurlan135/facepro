# FacePro Core Module
# Camera Thread, AI Thread, Re-ID Engine və Cleaner modullarını saxlayır

from .camera_thread import CameraWorker, CameraConfig, CameraManager
from .ai_thread import (
    AIWorker, 
    FrameResult, 
    Detection, 
    DetectionType,
    MotionDetector,
    ObjectDetector,
    FaceRecognizer,
    draw_detections
)
from .reid_engine import ReIDEngine, ReIDMatch, get_reid_engine
from .cleaner import StorageCleaner, get_cleaner

__all__ = [
    # Camera
    'CameraWorker', 'CameraConfig', 'CameraManager',
    # AI
    'AIWorker', 'FrameResult', 'Detection', 'DetectionType',
    'MotionDetector', 'ObjectDetector', 'FaceRecognizer', 'draw_detections',
    # Re-ID
    'ReIDEngine', 'ReIDMatch', 'get_reid_engine',
    # Cleaner
    'StorageCleaner', 'get_cleaner',
]

