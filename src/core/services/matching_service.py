
import numpy as np
from typing import List, Tuple, Optional, Any
from src.utils.logger import get_logger
from src.core.reid_engine import get_reid_engine
from src.core.gait_engine import get_gait_engine

logger = get_logger()

class MatchingService:
    """
    Service responsible for Vector Operations and In-Memory Matching.
    Acts as a Vector Database Cache (Matrix Store).
    
    Responsibilities:
    - Storing Embedding Matrices (Re-ID, Gait)
    - Computing Cosine Similarity / Euclidean Distance
    - Finding Nearest Neighbors
    """
    def __init__(self):
        # Engines (for comparison logic)
        self._reid_engine = get_reid_engine()
        self._gait_engine = get_gait_engine()
        
        # In-Memory Vector Stores (Matrices)
        # Structure: List of (id, user_id, name, vector)
        self._reid_cache: List[Tuple[int, int, str, np.ndarray]] = []
        self._gait_cache: List[Tuple[int, int, str, np.ndarray]] = []
        
        # Numpy Matrices for Vectorized Operations
        self._reid_matrix: Optional[np.ndarray] = None
        self._gait_matrix: Optional[np.ndarray] = None
        
        logger.info("MatchingService initialized")

    def load_reid_data(self, embeddings: List[Tuple[int, int, str, np.ndarray]]):
        """Loads bulk Re-ID data into cache."""
        self._reid_cache = embeddings
        if self._reid_cache:
            self._reid_matrix = np.vstack([item[3] for item in self._reid_cache])
        else:
            self._reid_matrix = None

    def load_gait_data(self, embeddings: List[Tuple[int, int, str, np.ndarray]]):
        """Loads bulk Gait data into cache."""
        self._gait_cache = embeddings
        if self._gait_cache:
            self._gait_matrix = np.vstack([item[3] for item in self._gait_cache])
        else:
            self._gait_matrix = None

    def add_reid_vector(self, user_id: int, name: str, vector: np.ndarray):
        """Adds a new Re-ID vector to the in-memory index."""
        # Add to list
        # Using 0 as placeholder ID since it's RAM-only until next reload
        self._reid_cache.append((0, user_id, name, vector))
        
        # Update Matrix
        if self._reid_matrix is None:
            self._reid_matrix = np.vstack([vector])
        else:
            self._reid_matrix = np.vstack([self._reid_matrix, vector])

    def add_gait_vector(self, user_id: int, name: str, vector: np.ndarray):
        """Adds a new Gait vector to the in-memory index."""
        self._gait_cache.append((0, user_id, name, vector))
        
        if self._gait_matrix is None:
            self._gait_matrix = np.vstack([vector])
        else:
            self._gait_matrix = np.vstack([self._gait_matrix, vector])

    def match_reid(self, vector: np.ndarray):
        """Finds best match for Re-ID vector."""
        if self._reid_matrix is None:
            return None
            
        # Use Engine's logic but provide the cached matrix
        return self._reid_engine.compare_embeddings(
            vector, 
            self._reid_cache,
            stored_matrix=self._reid_matrix
        )

    def match_gait(self, vector: np.ndarray):
        """Finds best match for Gait vector."""
        if self._gait_matrix is None:
            return None

        return self._gait_engine.compare_embeddings(
            vector, 
            self._gait_cache,
            stored_matrix=self._gait_matrix
        )
