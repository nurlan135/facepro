
from typing import List, Tuple, Optional, Any
from src.core.database.db_manager import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger()

class EventRepository:
    """
    Repository for managing 'events' table.
    """
    def __init__(self):
        self.db = DatabaseManager()

    def add_event(self, event_type: str, object_label: str = None, 
                  confidence: float = None, snapshot_path: str = None, 
                  identification_method: str = 'unknown') -> bool:
        """
        Log a new detection event.
        """
        query = """
            INSERT INTO events (event_type, object_label, confidence, snapshot_path, identification_method)
            VALUES (?, ?, ?, ?, ?)
        """
        success = self.db.execute_write(query, (event_type, object_label, confidence, snapshot_path, identification_method))
        if success:
             # Reduce log level to prevent spam
             # logger.debug(f"Event saved: {event_type} - {object_label}")
             pass
        return success
    
    def get_recent_events(self, limit: int = 50) -> List[Tuple]:
        """Fetch recent events for UI display."""
        query = """
            SELECT id, event_type, object_label, confidence, snapshot_path, identification_method, created_at
            FROM events
            ORDER BY created_at DESC
            LIMIT ?
        """
        return self.db.execute_read(query, (limit,))

    def get_events_count(self) -> int:
        query = "SELECT COUNT(*) FROM events"
        res = self.db.execute_read(query)
        if res:
            return res[0][0]
        return 0

    def get_all_events_for_export(self, limit: int = 1000) -> Tuple[List[str], List[Tuple]]:
        """Fetch rows for CSV export."""
        query = "SELECT * FROM events ORDER BY created_at DESC LIMIT ?"
        return self.db.execute_read_with_columns(query, (limit,))
