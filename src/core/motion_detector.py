"""
FacePro Motion Detection Module
Hərəkət aşkarlama - CPU qənaəti üçün AI-dən əvvəl işləyir.
"""

import cv2
import numpy as np

from src.utils.logger import get_logger

logger = get_logger()


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
