
import numpy as np
from typing import List, Tuple, Optional
from src.core.database.db_manager import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger()

class EmbeddingRepository:
    """
    Repository for handling vector embeddings (Face, Re-ID, Gait).
    Centralizes binary serialization and storage logic.
    """
    def __init__(self):
        self.db = DatabaseManager()

    # ================= Face Encodings =================
    
    def add_face_encoding(self, user_id: int, encoding: np.ndarray):
        """Save a face encoding (128d vector) to DB."""
        query = "INSERT INTO face_encodings (user_id, encoding) VALUES (?, ?)"
        # Default to float32 for storage efficiency if model allows, but usually dlib produces float64.
        # We store as providing, but it's good practice to stick to one. 
        # Existing code handles both. We'll store what we get.
        blob = encoding.tobytes()
        return self.db.execute_write(query, (user_id, blob))

    def get_all_face_encodings(self) -> List[Tuple[int, np.ndarray]]:
        """
        Get all face encodings.
        Returns: List of (user_id, numpy_matrix)
        """
        query = "SELECT user_id, encoding FROM face_encodings"
        rows = self.db.execute_read(query)
        encodings = []
        
        expected_size_f64 = 128 * 8
        expected_size_f32 = 128 * 4

        for uid, blob in rows:
            try:
                if len(blob) == expected_size_f64:
                    arr = np.frombuffer(blob, dtype=np.float64).copy()
                elif len(blob) == expected_size_f32:
                    arr = np.frombuffer(blob, dtype=np.float32).copy()
                else:
                    # Possibly legacy or corrupt. Skip or log.
                    continue
                encodings.append((uid, arr))
            except Exception:
                pass
        return encodings

    def get_all_face_encodings_with_names(self) -> List[Tuple[int, str, np.ndarray]]:
        """
        Get all face encodings joined with user names.
        Returns: List of (user_id, name, numpy_matrix)
        """
        query = """
            SELECT u.id, u.name, fe.encoding
            FROM users u
            JOIN face_encodings fe ON u.id = fe.user_id
        """
        rows = self.db.execute_read(query)
        results = []
        
        expected_size_f64 = 128 * 8
        expected_size_f32 = 128 * 4

        for uid, name, blob in rows:
            try:
                if len(blob) == expected_size_f64:
                    arr = np.frombuffer(blob, dtype=np.float64).copy()
                elif len(blob) == expected_size_f32:
                    arr = np.frombuffer(blob, dtype=np.float32).copy()
                else:
                    continue
                results.append((uid, name, arr))
            except Exception:
                pass
        return results

    # ================= Re-ID Embeddings =================

    def add_reid_embedding(self, user_id: int, vector: np.ndarray, confidence: float):
        """Save Re-ID body vector (1280d usually)."""
        query = """
            INSERT INTO reid_embeddings (user_id, vector, confidence) 
            VALUES (?, ?, ?)
        """
        # Ensure float32 for ReID/EfficientNet
        blob = vector.astype(np.float32).tobytes()
        self.db.execute_write(query, (user_id, blob, confidence))

    def get_all_reid_embeddings(self) -> List[Tuple[int, int, np.ndarray]]:
        """
        Get all Re-ID embeddings.
        Returns: List of (id, user_id, numpy_vector)
        """
        query = "SELECT id, user_id, vector FROM reid_embeddings"
        rows = self.db.execute_read(query)
        results = []
        for row_id, uid, blob in rows:
            try:
                # EfficientNet 1280 dim * 4 bytes = 5120 bytes
                arr = np.frombuffer(blob, dtype=np.float32).copy()
                results.append((row_id, uid, arr))
            except Exception:
                pass
        return results

    def get_reid_embeddings_with_names(self) -> List[Tuple[int, int, str, np.ndarray]]:
        """
        Get Re-ID embeddings with user names.
        Returns: List of (id, user_id, user_name, numpy_vector)
        """
        query = """
            SELECT re.id, re.user_id, u.name, re.vector
            FROM reid_embeddings re 
            JOIN users u ON re.user_id = u.id
        """
        rows = self.db.execute_read(query)
        results = []
        for row_id, uid, name, blob in rows:
            try:
                arr = np.frombuffer(blob, dtype=np.float32).copy()
                results.append((row_id, uid, name, arr))
            except Exception:
                pass
        return results

    # ================= Gait Embeddings =================

    def add_gait_embedding(self, user_id: int, embedding: np.ndarray, confidence: float = 1.0):
        """Save Gait vector with FIFO limit (Max 10 per user)."""
        # Check count
        count_query = "SELECT COUNT(*) FROM gait_embeddings WHERE user_id = ?"
        res = self.db.execute_read(count_query, (user_id,))
        count = res[0][0] if res else 0
        
        MAX_EMBEDDINGS = 10
        if count >= MAX_EMBEDDINGS:
            # Delete oldest
            delete_query = """
                DELETE FROM gait_embeddings WHERE id IN (
                    SELECT id FROM gait_embeddings WHERE user_id = ? 
                    ORDER BY captured_at ASC LIMIT ?
                )
            """
            to_delete = count - MAX_EMBEDDINGS + 1
            self.db.execute_write(delete_query, (user_id, to_delete))

        query = """
            INSERT INTO gait_embeddings (user_id, embedding, confidence)
            VALUES (?, ?, ?)
        """
        blob = embedding.astype(np.float32).tobytes()
        return self.db.execute_insert(query, (user_id, blob, confidence))

    def get_all_gait_embeddings(self) -> List[Tuple[int, np.ndarray]]:
        """
        Get gait embeddings.
        Returns: List of (user_id, numpy_vector)
        """
        query = "SELECT user_id, embedding FROM gait_embeddings"
        rows = self.db.execute_read(query)
        results = []
        for uid, blob in rows:
            try:
                arr = np.frombuffer(blob, dtype=np.float32).copy()
                results.append((uid, arr))
            except Exception:
                pass
        return results

    def get_gait_embeddings_with_names(self) -> List[Tuple[int, int, str, np.ndarray]]:
        """
        Get Gait embeddings with names.
        Returns: List of (id, user_id, name, embedding)
        """
        query = """
            SELECT ge.id, ge.user_id, u.name, ge.embedding
            FROM gait_embeddings ge JOIN users u ON ge.user_id = u.id
            ORDER BY ge.user_id, ge.captured_at DESC
        """
        rows = self.db.execute_read(query)
        results = []
        for row_id, uid, name, blob in rows:
            try:
                arr = np.frombuffer(blob, dtype=np.float32).copy()
                results.append((row_id, uid, name, arr))
            except Exception:
                pass
        return results

    # ================= Management Helpers =================

    def get_embedding_ids(self, table: str, user_id: int) -> List[int]:
        """Get IDs of embeddings for a user from a specific table."""
        if table not in ('face_encodings', 'reid_embeddings', 'gait_embeddings'):
            return []
        query = f"SELECT id FROM {table} WHERE user_id = ?"
        rows = self.db.execute_read(query, (user_id,))
        return [r[0] for r in rows]

    def delete_embedding(self, table: str, embedding_id: int) -> bool:
        """Delete specific embedding by ID."""
        if table not in ('face_encodings', 'reid_embeddings', 'gait_embeddings'):
            return False
        query = f"DELETE FROM {table} WHERE id = ?"
        return self.db.execute_write(query, (embedding_id,))
