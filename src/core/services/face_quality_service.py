"""
FacePro Face Quality Service
Utility to validate face image quality before enrollment.
"""

import cv2
import numpy as np
from typing import Tuple, Optional

class FaceQualityService:
    """Evaluates face image quality based on blur, size, and multiple detections."""
    
    def __init__(self, blur_threshold: float = 100.0, min_face_size: int = 80):
        self.blur_threshold = blur_threshold
        self.min_face_size = min_face_size

    def check_quality(self, face_image: np.ndarray) -> Tuple[bool, str, float]:
        """
        Check quality of a cropped face image.
        
        Returns:
            (is_good, message, score)
        """
        if face_image is None or face_image.size == 0:
            return False, "Şəkil tapılmadı", 0.0
            
        # 1. Size Check
        h, w = face_image.shape[:2]
        if h < self.min_face_size or w < self.min_face_size:
            return False, f"Üz çox kiçikdir ({w}x{h}). Minimum: {self.min_face_size}x{self.min_face_size}", 0.0
            
        # 2. Blur Detection (Laplacian Variance)
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if variance < self.blur_threshold:
            return False, f"Şəkil çox bulanıqdır (V:{variance:.1f}). Zəhmət olmasa daha aydın şəkil çəkin.", variance
            
        # 3. Brightness check (Optional)
        avg_brightness = np.mean(gray)
        if avg_brightness < 40:
            return False, "Şəkil çox qaranlıqdır.", avg_brightness
        if avg_brightness > 220:
            return False, "Şəkil çox parlaqdır.", avg_brightness
            
        return True, "Keyfiyyət yaxşıdır", variance

    @staticmethod
    def get_blur_score(image: np.ndarray) -> float:
        """Returns the Laplacian variance score."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
