"""
FacePro Audit Logger
Utility for tracking administrative and security-sensitive actions.
"""

import json
import threading
from typing import Any, Dict, Optional
from datetime import datetime

from src.core.database.db_manager import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger()

class AuditLogger:
    """Singleton for logging security and admin events to the database"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AuditLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
            
    def __init__(self):
        if self._initialized:
            return
        self._db = DatabaseManager()
        self._initialized = True
        
    def log(self, action_type: str, details: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None):
        """
        Record an action in the audit trail.
        
        Args:
            action_type: Category of action (e.g., 'LOGIN', 'SETTINGS_CHANGE')
            details: Dictionary containing specific data about the action
            user_id: ID of the user performing the action (if None, attempts to auto-resolve from session)
        """
        try:
            # Try to get user_id from Session if not provided
            if user_id is None:
                from src.utils.auth_manager import get_auth_manager
                auth_manager = get_auth_manager()
                current_user = auth_manager.get_current_user()
                if current_user:
                    user_id = current_user.user_id
            
            details_json = json.dumps(details) if details else None
            
            query = """
                INSERT INTO audit_logs (user_id, action_type, details, created_at)
                VALUES (?, ?, ?, ?)
            """
            self._db.execute_write(query, (user_id, action_type, details_json, datetime.now().isoformat()))
            
            logger.info(f"AUDIT: [{action_type}] User: {user_id} - {details if details else ''}")
            
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

    def get_logs(self, limit: int = 100, offset: int = 0) -> list:
        """Retrieve historical audit logs with user names"""
        query = """
            SELECT al.id, al.action_type, al.details, al.created_at, au.username
            FROM audit_logs al
            LEFT JOIN app_users au ON al.user_id = au.id
            ORDER BY al.created_at DESC
            LIMIT ? OFFSET ?
        """
        try:
            results = self._db.execute_read(query, (limit, offset))
            # Format results into list of dicts
            logs = []
            for row in results:
                logs.append({
                    'id': row[0],
                    'action': row[1],
                    'details': json.loads(row[2]) if row[2] else {},
                    'timestamp': row[3],
                    'username': row[4] or "System"
                })
            return logs
        except Exception as e:
            logger.error(f"Failed to fetch audit logs: {e}")
            return []

def get_audit_logger() -> AuditLogger:
    return AuditLogger()
