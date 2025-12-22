"""
FacePro Storage Worker Module
Handles asynchronous disk I/O (snapshots) and database writing (events, embeddings)
to prevent blocking the Main Thread or AI Thread.
"""
import time
import queue
import threading
from enum import Enum, auto
from typing import Optional, Tuple, Any, Dict

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from src.utils.logger import get_logger
from src.utils.helpers import save_snapshot
from src.core.database.repositories.event_repository import EventRepository
from src.core.database.repositories.embedding_repository import EmbeddingRepository
from src.core.detection import Detection

logger = get_logger()

class TaskType(Enum):
    EVENT = auto()
    REID = auto()
    GAIT = auto()

class StorageWorker(QThread):
    """
    Dedicated thread for blocking I/O operations.
    - Saves event snapshots to disk
    - Saves event metadata to SQLite
    - Saves Re-ID and Gait embeddings to SQLite
    """
    
    event_saved = pyqtSignal(int)
    
    # Optional: Signals for embedding saves if UI needs update
    reid_saved = pyqtSignal(int, int) # user_id, row_id
    gait_saved = pyqtSignal(int, int) # user_id, row_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._task_queue = queue.Queue()
        
        # Repositories
        self._event_repo = EventRepository()
        self._embedding_repo = EmbeddingRepository()
        
        logger.info("StorageWorker initialized")

    def run(self):
        """Main loop processing the queue."""
        self._running = True
        logger.info("StorageWorker started")
        
        while self._running:
            try:
                task = self._task_queue.get(timeout=0.5)
                if task is None: continue
                    
                self._process_task(task)
                self._task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"StorageWorker loop error: {e}")
        
        logger.info("StorageWorker stopped")

    def _process_task(self, task: Dict[str, Any]):
        task_type = task.get('type')
        data = task.get('data')
        
        try:
            if task_type == TaskType.EVENT:
                self._handle_event_task(data)
            elif task_type == TaskType.REID:
                self._handle_reid_task(data)
            elif task_type == TaskType.GAIT:
                self._handle_gait_task(data)
            else:
                logger.warning(f"Unknown task type: {task_type}")
        except Exception as e:
            logger.error(f"Failed to process storage task ({task_type}): {e}")

    def _handle_event_task(self, data):
        detection = data['detection']
        frame = data['frame']
        
        # Save Snapshot
        snapshot_path = save_snapshot(frame, folder='logs', prefix=f"event_{detection.label}")
        
        # Save to DB
        event_type = detection.type.value if hasattr(detection.type, 'value') else str(detection.type)
        identification_method = getattr(detection, 'identification_method', 'unknown')
        
        event_id = self._event_repo.add_event(
            event_type=event_type,
            object_label=detection.label,
            confidence=detection.confidence,
            snapshot_path=snapshot_path,
            identification_method=identification_method
        )
        
        if event_id:
            self.event_saved.emit(event_id)

    def _handle_reid_task(self, data):
        user_id = data['user_id']
        vector = data['vector']
        confidence = data['confidence']
        
        # Using the atomic repository method
        self._embedding_repo.add_reid_embedding(user_id, vector, confidence)

    def _handle_gait_task(self, data):
        user_id = data['user_id']
        embedding = data['embedding']
        confidence = data['confidence']
        
        # Using the atomic repository method
        row_id = self._embedding_repo.add_gait_embedding(user_id, embedding, confidence)
        if row_id:
            self.gait_saved.emit(user_id, row_id)

    # ================= Public API =================

    def add_event_task(self, detection: Detection, frame: np.ndarray):
        """Queue an event (detection) to be saved."""
        if not self._running: return
        # Copy frame to avoid modification during queue wait
        frame_copy = frame.copy() if frame is not None else None
        
        self._task_queue.put({
            'type': TaskType.EVENT,
            'data': {
                'detection': detection,
                'frame': frame_copy,
                'timestamp': time.time()
            }
        })
    
    # Backward compatibility alias (can be removed later)
    def add_task(self, detection: Detection, frame: np.ndarray):
        self.add_event_task(detection, frame)

    def add_reid_task(self, user_id: int, vector: np.ndarray, confidence: float = 1.0):
        """Queue a Re-ID embedding to be saved."""
        if not self._running: return
        self._task_queue.put({
            'type': TaskType.REID,
            'data': {
                'user_id': user_id,
                'vector': vector.copy(), # Ensure isolated copy
                'confidence': confidence
            }
        })

    def add_gait_task(self, user_id: int, embedding: np.ndarray, confidence: float = 1.0):
        """Queue a Gait embedding to be saved."""
        if not self._running: return
        self._task_queue.put({
            'type': TaskType.GAIT,
            'data': {
                'user_id': user_id,
                'embedding': embedding.copy(), # Ensure isolated copy
                'confidence': confidence
            }
        })

    def stop(self):
        self._running = False
        self.wait(1000)
