"""
FacePro Detection Data Classes
Aşkarlama nəticələri üçün data strukturları.
"""

from typing import List, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


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
    track_id: int = -1  # YOLO track ID for gait recognition
    identification_method: str = ""  # 'face', 'reid', 'gait' - which method identified the person


@dataclass
class FrameResult:
    """Frame emalı nəticəsi."""
    frame: np.ndarray
    detections: List[Detection] = field(default_factory=list)
    motion_detected: bool = False
    processing_time_ms: float = 0.0
    camera_name: str = ""
