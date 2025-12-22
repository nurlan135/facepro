
from typing import Optional, List, Tuple
from src.core.database.db_manager import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger()

class UserRepository:
    """
    Repository for managing 'users' table (People recognized by the system).
    Not to be confused with 'app_users' (System operators).
    """
    def __init__(self):
        self.db = DatabaseManager()

    def get_user_id_by_name(self, name: str) -> Optional[int]:
        """Find user ID by name."""
        query = "SELECT id FROM users WHERE name = ?"
        results = self.db.execute_read(query, (name,))
        if results:
            return results[0][0]
        return None

    def create_user(self, name: str) -> Optional[int]:
        """Create a new user if not exists."""
        # Check existence first
        existing_id = self.get_user_id_by_name(name)
        if existing_id:
            return existing_id

        insert_query = "INSERT INTO users (name) VALUES (?)"
        if self.db.execute_write(insert_query, (name,)):
            return self.get_user_id_by_name(name)
        return None
    
    def get_users_with_stats(self) -> List[Tuple[int, str, int, int]]:
        """
        Get all users with their embedding counts.
        Returns: [(id, name, face_count, body_count), ...]
        """
        query = """
            SELECT u.id, u.name,
                   (SELECT COUNT(*) FROM face_encodings WHERE user_id = u.id) as face_count,
                   (SELECT COUNT(*) FROM reid_embeddings WHERE user_id = u.id) as body_count
            FROM users u
            ORDER BY u.name
        """
        rows = self.db.execute_read(query)
        # rows is list of tuples
        return rows

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user and cascading data manually (if FK cascade not set).
        """
        # Execute deletions in transaction (handled by db_manager locks, but we do sequential writes)
        # Ideally this should be a single transaction. 
        # But db_manager execute_write commits immediately.
        # We'll rely on foreign keys if possible, but to be safe we delete children first.
        
        try:
            self.db.execute_write("DELETE FROM face_encodings WHERE user_id = ?", (user_id,))
            self.db.execute_write("DELETE FROM reid_embeddings WHERE user_id = ?", (user_id,))
            self.db.execute_write("DELETE FROM gait_embeddings WHERE user_id = ?", (user_id,))
            return self.db.execute_write("DELETE FROM users WHERE id = ?", (user_id,))
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    def get_user_count(self) -> int:
        query = "SELECT COUNT(*) FROM users"
        res = self.db.execute_read(query)
        if res:
            return res[0][0]
        return 0
