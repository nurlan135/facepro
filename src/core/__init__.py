# FacePro Core Module
# Camera Thread, AI Thread, Re-ID Engine, Gait Engine və Cleaner modullarını saxlayır

from .camera_thread import CameraWorker, CameraConfig, CameraManager

# Detection data classes (modular)
from .detection import Detection, DetectionType, FrameResult

# AI components (modular)
from .motion_detector import MotionDetector
from .object_detector import ObjectDetector
from .face_recognizer import FaceRecognizer
from .ai_thread import AIWorker, draw_detections

# Re-ID
from .reid_engine import ReIDEngine, ReIDMatch, get_reid_engine

# Gait Recognition
from .gait_types import GaitBuffer, GaitMatch
from .gait_buffer import GaitBufferManager
from .gait_engine import GaitEngine, get_gait_engine

# Cleaner
from .cleaner import StorageCleaner, get_cleaner

__all__ = [
    # Camera
    'CameraWorker', 'CameraConfig', 'CameraManager',
    # Detection
    'Detection', 'DetectionType', 'FrameResult',
    # AI Components
    'MotionDetector', 'ObjectDetector', 'FaceRecognizer',
    'AIWorker', 'draw_detections',
    # Re-ID
    'ReIDEngine', 'ReIDMatch', 'get_reid_engine',
    # Gait
    'GaitBuffer', 'GaitMatch', 'GaitBufferManager', 'GaitEngine', 'get_gait_engine',
    # Cleaner
    'StorageCleaner', 'get_cleaner',
]
