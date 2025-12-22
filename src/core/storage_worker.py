"""
FacePro Storage Worker Module
Handles asynchronous disk I/O (snapshots) and database writing (events)
to prevent blocking the Main Thread or AI Thread.
"""
import time
import queue
import threading
from typing import Optional, Tuple

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

from src.utils.logger import get_logger
from src.utils.helpers import save_snapshot
from src.core.database.repositories.event_repository import EventRepository
from src.core.detection import Detection, DetectionType

logger = get_logger()

class StorageWorker(QThread):
    """
    Dedicated thread for blocking I/O operations.
    - Saves event snapshots to disk
    - Saves event metadata to SQLite
    """
    
    event_saved = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._task_queue = queue.Queue()
        self._event_repo = EventRepository()
        
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

    def _process_task(self, task):
        try:
            detection, frame, timestamp = task
            camera_name = getattr(detection, 'camera_name', 'Unknown')
            
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
            
        except Exception as e:
            logger.error(f"Failed to process storage task: {e}")

    def add_task(self, detection: Detection, frame: np.ndarray):
        if not self._running: return
        frame_copy = frame.copy() if frame is not None else None
        self._task_queue.put((detection, frame_copy, time.time()))

    def stop(self):
        self._running = False
        self.wait(1000)
