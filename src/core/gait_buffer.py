"""
FacePro Gait Buffer Manager
Hər track_id üçün silhouette buffer idarəsi.
"""

import time
from typing import Optional, List, Dict

import numpy as np

from src.utils.logger import get_logger
from src.core.gait_types import GaitBuffer

logger = get_logger()


class GaitBufferManager:
    """
    Hər track_id üçün silhouette buffer idarəsi.
    Manages separate gait buffers for each tracked person.
    """
    
    def __init__(self, sequence_length: int = 30, timeout: float = 5.0):
        """
        Args:
            sequence_length: Analiz üçün lazım olan frame sayı
            timeout: Buffer timeout (saniyə)
        """
        self._buffers: Dict[int, GaitBuffer] = {}
        self._sequence_length = sequence_length
        self._timeout = timeout
    
    def add_frame(self, track_id: int, silhouette: np.ndarray) -> bool:
        """
        Buffer-ə frame əlavə et.
        
        Args:
            track_id: YOLO track ID
            silhouette: 64x64 silhouette şəkli
            
        Returns:
            True əgər buffer dolubsa (sequence_length-ə çatıb)
        """
        if track_id not in self._buffers:
            self._buffers[track_id] = GaitBuffer(track_id=track_id)
        
        buffer = self._buffers[track_id]
        buffer.silhouettes.append(silhouette)
        buffer.last_update = time.time()
        
        return len(buffer.silhouettes) >= self._sequence_length
    
    def get_sequence(self, track_id: int) -> Optional[List[np.ndarray]]:
        """
        Tam seqansı qaytar və buffer-i təmizlə.
        
        Args:
            track_id: YOLO track ID
            
        Returns:
            Silhouette siyahısı və ya None
        """
        if track_id not in self._buffers:
            return None
        
        buffer = self._buffers[track_id]
        if len(buffer.silhouettes) < self._sequence_length:
            return None
        
        sequence = buffer.silhouettes[:self._sequence_length]
        del self._buffers[track_id]
        
        return sequence
    
    def cleanup_stale(self):
        """Timeout keçmiş buffer-ləri sil."""
        current_time = time.time()
        stale_ids = [
            track_id for track_id, buffer in self._buffers.items()
            if current_time - buffer.last_update > self._timeout
        ]
        
        for track_id in stale_ids:
            del self._buffers[track_id]
            logger.debug(f"Stale gait buffer removed: track_id={track_id}")
    
    def get_buffer_size(self, track_id: int) -> int:
        """Track ID üçün buffer ölçüsünü qaytar."""
        if track_id not in self._buffers:
            return 0
        return len(self._buffers[track_id].silhouettes)
    
    def clear(self):
        """Bütün buffer-ləri təmizlə."""
        self._buffers.clear()
