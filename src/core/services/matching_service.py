
import numpy as np
from typing import List, Tuple, Optional, Any, TYPE_CHECKING
from src.utils.logger import get_logger
from src.core.reid_engine import get_reid_engine, ReIDEngine
from src.core.gait_engine import get_gait_engine, GaitEngine

logger = get_logger()

class MatchingService:
    """
    Service responsible for Vector Operations and In-Memory Matching.
    Acts as a Vector Database Cache (Matrix Store).
    
    Responsibilities:
    - Storing Embedding Matrices (Re-ID, Gait)
    - Computing Cosine Similarity / Euclidean Distance
    - Finding Nearest Neighbors
    
    Supports Dependency Injection for testing:
        service = MatchingService(reid_engine=mock_reid, gait_engine=mock_gait)
    """
    def __init__(
        self, 
        reid_engine: Optional[ReIDEngine] = None,
        gait_engine: Optional[GaitEngine] = None
    ):
        # DI: Use injected engines or fall back to singletons
        self._reid_engine = reid_engine or get_reid_engine()
        self._gait_engine = gait_engine or get_gait_engine()
        
        # In-Memory Vector Stores (Matrices)
        # Structure: List of (id, user_id, name, vector)
        self._reid_cache: List[Tuple[int, int, str, np.ndarray]] = []
        self._gait_cache: List[Tuple[int, int, str, np.ndarray]] = []
        
        # Numpy Matrices for Vectorized Operations
        self._reid_matrix: Optional[np.ndarray] = None
        self._gait_matrix: Optional[np.ndarray] = None
        
        # PERFORMANCE: Lazy rebuild flags - matrix only rebuilt when needed
        self._reid_matrix_dirty = False
        self._gait_matrix_dirty = False
        
        logger.info("MatchingService initialized")

    def load_reid_data(self, embeddings: List[Tuple[int, int, str, np.ndarray]]):
        """Loads bulk Re-ID data into cache."""
        valid_embeddings = []
        expected_dim = self._reid_engine.embedding_size if hasattr(self._reid_engine, 'embedding_size') else 1280
        
        for item in embeddings:
            if item[3].shape[0] == expected_dim:
                valid_embeddings.append(item)
            else:
                logger.warning(f"Skipping Re-ID embedding for user '{item[2]}' due to dimension mismatch: expected {expected_dim}, got {item[3].shape[0]}")
        
        self._reid_cache = valid_embeddings
        if self._reid_cache:
            try:
                self._reid_matrix = np.vstack([item[3] for item in self._reid_cache])
            except Exception as e:
                logger.error(f"Failed to build Re-ID matrix: {e}")
                self._reid_matrix = None
        else:
            self._reid_matrix = None

    def load_gait_data(self, embeddings: List[Tuple[int, int, str, np.ndarray]]):
        """Loads bulk Gait data into cache."""
        valid_embeddings = []
        # Gait usually uses 512 from ResNet18-based adapter
        expected_dim = self._gait_engine.embedding_size if hasattr(self._gait_engine, 'embedding_size') else 512
        
        for item in embeddings:
            if item[3].shape[0] == expected_dim:
                valid_embeddings.append(item)
            else:
                logger.warning(f"Skipping Gait embedding for user '{item[2]}' due to dimension mismatch: expected {expected_dim}, got {item[3].shape[0]}")

        self._gait_cache = valid_embeddings
        if self._gait_cache:
            try:
                self._gait_matrix = np.vstack([item[3] for item in self._gait_cache])
            except Exception as e:
                logger.error(f"Failed to build Gait matrix: {e}")
                self._gait_matrix = None
        else:
            self._gait_matrix = None

    def add_reid_vector(self, user_id: int, name: str, vector: np.ndarray):
        """Adds a new Re-ID vector to the in-memory index."""
        expected_dim = getattr(self._reid_engine, 'embedding_size', 1280)
        if vector.shape[0] != expected_dim:
            logger.error(f"Cannot add Re-ID vector for {name}: Dimension mismatch. Expected {expected_dim}, got {vector.shape[0]}")
            return

        # Add to list
        self._reid_cache.append((0, user_id, name, vector))
        
        # PERFORMANCE: Mark dirty instead of immediate rebuild (O(1) vs O(N))
        self._reid_matrix_dirty = True

    def add_gait_vector(self, user_id: int, name: str, vector: np.ndarray):
        """Adds a new Gait vector to the in-memory index."""
        expected_dim = getattr(self._gait_engine, 'embedding_size', 256)
        if vector.shape[0] != expected_dim:
            logger.error(f"Cannot add Gait vector for {name}: Dimension mismatch. Expected {expected_dim}, got {vector.shape[0]}")
            return

        self._gait_cache.append((0, user_id, name, vector))
        
        # PERFORMANCE: Mark dirty instead of immediate rebuild (O(1) vs O(N))
        self._gait_matrix_dirty = True
    
    def _ensure_reid_matrix(self):
        """Lazily rebuild Re-ID matrix only when dirty."""
        if self._reid_matrix_dirty and self._reid_cache:
            self._reid_matrix = np.vstack([item[3] for item in self._reid_cache])
            self._reid_matrix_dirty = False
    
    def _ensure_gait_matrix(self):
        """Lazily rebuild Gait matrix only when dirty."""
        if self._gait_matrix_dirty and self._gait_cache:
            self._gait_matrix = np.vstack([item[3] for item in self._gait_cache])
            self._gait_matrix_dirty = False

    def match_reid(self, vector: np.ndarray):
        """Finds best match for Re-ID vector."""
        # PERFORMANCE: Lazy rebuild on match, not on add
        self._ensure_reid_matrix()
        
        if self._reid_matrix is None or len(self._reid_cache) == 0:
            return None
            
        # Use Engine's logic but provide the cached matrix
        return self._reid_engine.compare_embeddings(
            vector, 
            self._reid_cache,
            stored_matrix=self._reid_matrix
        )

    def match_gait(self, vector: np.ndarray):
        """Finds best match for Gait vector."""
        # PERFORMANCE: Lazy rebuild on match, not on add
        self._ensure_gait_matrix()
        
        if self._gait_matrix is None or len(self._gait_cache) == 0:
            return None

        return self._gait_engine.compare_embeddings(
            vector, 
            self._gait_cache,
            stored_matrix=self._gait_matrix
        )
