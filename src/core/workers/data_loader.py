
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from typing import List, Tuple, Any, Optional
from src.core.database.repositories.event_repository import EventRepository
from src.utils.logger import get_logger

logger = get_logger()

class DataLoaderWorker(QThread):
    """
    Worker thread to load data from database asynchronously.
    Prevents UI freezing during large data fetches.
    """
    # Signals
    events_loaded = pyqtSignal(list, int, str) # events, total_count (approx or just valid flag), request_type
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._repo = EventRepository()
        self._request_type = None
        self._limit = 20
        self._offset = 0
        self._is_busy = False

    def load_events(self, limit: int = 20, offset: int = 0, request_type: str = "initial"):
        """
        Starts the thread to load events.
        request_type: "initial" or "more" to help UI distinguish response
        """
        if self.isRunning():
            logger.warning("DataLoaderWorker is already running. Request ignored.")
            return

        self._limit = limit
        self._offset = offset
        self._request_type = request_type
        self.start()

    def run(self):
        """
        Thread execution entry point.
        """
        self._is_busy = True
        try:
            if self._request_type == "initial" or self._request_type == "more":
                # Get events
                if self._offset == 0 and self._request_type == "initial":
                    # For initial load, we might want recent events
                    events = self._repo.get_recent_events(limit=self._limit)
                else:
                    # Generic pagination
                    events = self._repo.get_events_paginated(limit=self._limit, offset=self._offset)
                
                # Emit results
                # Only returning list for now, total count is expensive so we skip or assume more might exist
                self.events_loaded.emit(events, len(events), self._request_type)
            
        except Exception as e:
            logger.error(f"Error in DataLoaderWorker: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self._is_busy = False
