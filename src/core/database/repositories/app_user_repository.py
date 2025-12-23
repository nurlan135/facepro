from typing import Optional, List, Tuple, Dict, Any
from src.core.database.db_manager import DatabaseManager

class AppUserRepository:
    """
    Repository for 'app_users' table (Login accounts).
    """

    def __init__(self):
        self.db = DatabaseManager()

    def create_user(self, username: str, password_hash: str, salt: str, role: str) -> bool:
        """Create a new app user."""
        query = """
            INSERT INTO app_users (username, password_hash, salt, role)
            VALUES (?, ?, ?, ?)
        """
        return self.db.execute_write(query, (username, password_hash, salt, role))

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username. Returns dict-like row."""
        query = """
            SELECT id, username, password_hash, salt, role, is_locked, 
                   lock_until, failed_attempts, created_at
            FROM app_users WHERE username = ?
        """
        columns, rows = self.db.execute_read_with_columns(query, (username,))
        if rows:
            return dict(zip(columns, rows[0]))
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        query = """
            SELECT id, username, password_hash, salt, role, is_locked, 
                   lock_until, failed_attempts, created_at
            FROM app_users WHERE id = ?
        """
        columns, rows = self.db.execute_read_with_columns(query, (user_id,))
        if rows:
            return dict(zip(columns, rows[0]))
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """List all users."""
        query = """
            SELECT id, username, password_hash, salt, role, is_locked, 
                   lock_until, failed_attempts, created_at
            FROM app_users
            ORDER BY created_at
        """
        columns, rows = self.db.execute_read_with_columns(query)
        return [dict(zip(columns, row)) for row in rows]

    # Security: Whitelist of allowed columns for update operations
    # This prevents SQL Injection when dynamically building UPDATE queries
    ALLOWED_UPDATE_COLUMNS = frozenset({
        'password_hash',
        'salt',
        'role',
        'is_locked',
        'lock_until',
        'failed_attempts'
    })

    def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update user fields.
        
        Security: Only columns in ALLOWED_UPDATE_COLUMNS can be updated.
        This prevents SQL Injection attacks via dynamic column names.
        
        Args:
            user_id: User ID to update
            updates: dict of {column: value} - only whitelisted columns allowed
            
        Returns:
            True if update was successful
            
        Raises:
            ValueError: If any column name is not in the whitelist
        """
        if not updates:
            return False
        
        # Security: Validate all column names against whitelist
        invalid_columns = set(updates.keys()) - self.ALLOWED_UPDATE_COLUMNS
        if invalid_columns:
            from src.utils.logger import get_logger
            logger = get_logger()
            logger.error(f"SQL Injection attempt blocked: Invalid columns {invalid_columns}")
            raise ValueError(f"Invalid column names: {invalid_columns}")
            
        set_parts = []
        params = []
        for col, val in updates.items():
            set_parts.append(f"{col} = ?")
            params.append(val)
        
        params.append(user_id)
        query = f"UPDATE app_users SET {', '.join(set_parts)} WHERE id = ?"
        return self.db.execute_write(query, tuple(params))

    def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        query = "DELETE FROM app_users WHERE id = ?"
        return self.db.execute_write(query, (user_id,))

    def get_admin_count(self) -> int:
        """Count admins."""
        query = "SELECT COUNT(*) FROM app_users WHERE role = 'admin'"
        res = self.db.execute_read(query)
        if res:
            return res[0][0]
        return 0
