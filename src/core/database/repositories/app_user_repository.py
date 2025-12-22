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

    def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update user fields.
        updates: dict of {column: value}
        """
        if not updates:
            return False
            
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
