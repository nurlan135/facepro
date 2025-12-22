"""
FacePro Gait Recognition Engine
Yeriş xüsusiyyətləri çıxarma və müqayisə.
Silhouette-based gait recognition using CNN feature extractor.
"""

import os
# Note: pickle removed for security - use numpy tobytes/frombuffer instead
from typing import Optional, List, Tuple

import cv2
import numpy as np

from src.utils.logger import get_logger
from src.core.gait_types import GaitMatch

logger = get_logger()

# Torch lazy loading
_torch = None
_torchvision = None


def _lazy_import_torch():
    """Torch-u lazy load edir."""
    global _torch, _torchvision
    if _torch is None:
        try:
            import torch
            import torchvision
            _torch = torch
            _torchvision = torchvision
            logger.info(f"PyTorch loaded for Gait: {torch.__version__}")
        except ImportError as e:
            logger.error(f"PyTorch import failed: {e}")
            raise
    return _torch, _torchvision


class GaitEngine:
    """
    Yeriş tanıma mühərriki.
    Silhouette-based gait recognition using CNN feature extractor.
    """
    
    # Constants
    SEQUENCE_LENGTH = 30
    SILHOUETTE_SIZE = (64, 64)
    EMBEDDING_DIM = 256
    DEFAULT_THRESHOLD = 0.70
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True):
        self._model = None
        self._device = None
        self._model_path = model_path
        self._use_gpu = use_gpu
        self._threshold = self.DEFAULT_THRESHOLD
        self._bg_subtractor = None
        self._enabled = True
        self._sequence_length = self.SEQUENCE_LENGTH
        
        self._load_settings()
        logger.info("GaitEngine created (lazy loading)")
    
    def _load_settings(self):
        """Load gait settings from settings.json."""
        try:
            from src.utils.helpers import load_config
            config = load_config()
            gait_config = config.get('gait', {})
            
            self._enabled = gait_config.get('enabled', True)
            self._threshold = gait_config.get('threshold', self.DEFAULT_THRESHOLD)
            self._sequence_length = gait_config.get('sequence_length', self.SEQUENCE_LENGTH)
            
            logger.info(f"Gait settings: enabled={self._enabled}, threshold={self._threshold}")
        except Exception as e:
            logger.warning(f"Failed to load gait settings: {e}")
    
    def reload_settings(self):
        """Reload settings from settings.json."""
        self._load_settings()
    
    def is_enabled(self) -> bool:
        return self._enabled
    
    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        logger.info(f"Gait recognition {'enabled' if enabled else 'disabled'}")
    
    def get_sequence_length(self) -> int:
        return self._sequence_length
    
    def set_sequence_length(self, length: int):
        self._sequence_length = max(20, min(60, length))
    
    def _ensure_loaded(self):
        """Model-in yükləndiyini təmin edir."""
        if self._model is not None:
            return
        
        torch, torchvision = _lazy_import_torch()
        
        if self._use_gpu and torch.cuda.is_available():
            self._device = torch.device('cuda')
            logger.info("Gait using GPU")
        else:
            self._device = torch.device('cpu')
            logger.info("Gait using CPU")
        
        try:
            if self._model_path and os.path.exists(self._model_path):
                # Security: weights_only=True prevents arbitrary code execution
                self._model = torch.load(
                    self._model_path, 
                    map_location=self._device,
                    weights_only=True
                )
                logger.info(f"Custom Gait model loaded: {self._model_path}")
            else:
                weights = torchvision.models.ResNet18_Weights.DEFAULT
                base_model = torchvision.models.resnet18(weights=weights)
                base_model.conv1 = torch.nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
                base_model.fc = torch.nn.Linear(512, self.EMBEDDING_DIM)
                self._model = base_model
                logger.info("Pretrained ResNet18 adapted for Gait")
            
            self._model = self._model.to(self._device)
            self._model.eval()
        except Exception as e:
            logger.error(f"Failed to load Gait model: {e}")
            raise
        
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=False)

    def extract_silhouette(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """Person bounding box-dan silhouette çıxar."""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(w, int(x2))
        y2 = min(h, int(y2))
        
        person_region = frame[y1:y2, x1:x2]
        
        if person_region.size == 0:
            return np.zeros(self.SILHOUETTE_SIZE, dtype=np.uint8)
        
        gray = cv2.cvtColor(person_region, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return cv2.resize(binary, self.SILHOUETTE_SIZE, interpolation=cv2.INTER_AREA)
    
    def extract_embedding(self, silhouettes: List[np.ndarray]) -> Optional[np.ndarray]:
        """30 silhouette-dən 256D embedding çıxar."""
        if len(silhouettes) < self.SEQUENCE_LENGTH:
            logger.warning(f"Not enough silhouettes: {len(silhouettes)}/{self.SEQUENCE_LENGTH}")
            return None
        
        try:
            self._ensure_loaded()
            torch, _ = _lazy_import_torch()
            
            silhouette_stack = np.stack(silhouettes[:self.SEQUENCE_LENGTH], axis=0)
            silhouette_stack = silhouette_stack.astype(np.float32) / 255.0
            
            silhouette_tensor = torch.from_numpy(silhouette_stack).unsqueeze(1)
            silhouette_tensor = silhouette_tensor.to(self._device)
            
            with torch.no_grad():
                # PERFORMANCE: Batch inference instead of frame-by-frame (10-30x faster)
                # Process all frames in a single forward pass - leverages GPU parallelism
                batch_embeddings = self._model(silhouette_tensor)  # Shape: (SEQUENCE_LENGTH, EMBEDDING_DIM)
                avg_embedding = torch.mean(batch_embeddings, dim=0, keepdim=True)
            
            embedding_np = avg_embedding.cpu().numpy().flatten()
            norm = np.linalg.norm(embedding_np)
            if norm > 0:
                embedding_np = embedding_np / norm
            
            return embedding_np
        except Exception as e:
            logger.error(f"Gait embedding extraction failed: {e}")
            return None

    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """İki embedding arasında cosine similarity."""
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(np.clip(dot_product / (norm1 * norm2), 0, 1))
        except Exception:
            return 0.0
    
    def compare_embeddings(
        self, 
        query_embedding: np.ndarray, 
        stored_embeddings: List[Tuple[int, int, str, np.ndarray]],
        stored_matrix: Optional[np.ndarray] = None
    ) -> Optional[GaitMatch]:
        """
        Query embedding-i saxlanılan embedding-lərlə müqayisə edir (Vectorized).
        
        Args:
            query_embedding: Sorğu embedding-i (1D array)
            stored_embeddings: Metadata list [(embedding_id, user_id, user_name, embedding), ...]
            stored_matrix: Opsional pre-built numpy matrix (N, D).
            
        Returns:
            Ən yaxşı uyğunluq (GaitMatch) və ya None
        """
        if not stored_embeddings:
            return None
            
        try:
            # 1. Prepare Matrix
            if stored_matrix is not None:
                matrix = stored_matrix
            else:
                matrix_list = [item[3] for item in stored_embeddings]
                matrix = np.vstack(matrix_list)
            
            # 2. Vectorized Cosine Similarity (assuming normalized vectors)
            scores = np.dot(matrix, query_embedding)
            
            # 3. Find Best Match
            best_idx = np.argmax(scores)
            best_score = float(scores[best_idx])
            
            if best_score >= self._threshold:
                emb_id, user_id, user_name, _ = stored_embeddings[best_idx]
                return GaitMatch(
                    user_id=user_id, 
                    user_name=user_name, 
                    confidence=best_score, 
                    embedding_id=emb_id
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Vectorized gait comparison failed: {e}")
            return None
    
    def set_threshold(self, threshold: float):
        self._threshold = max(0.0, min(1.0, threshold))
    
    def get_threshold(self) -> float:
        return self._threshold
    
    @staticmethod
    def serialize_embedding(embedding: np.ndarray) -> bytes:
        """Gait embedding-i SQLite BLOB üçün serialize edir (safe numpy format)."""
        return embedding.astype(np.float32).tobytes()
    
    @staticmethod
    def deserialize_embedding(blob: bytes, expected_dim: int = 256) -> np.ndarray:
        """
        BLOB-dan gait embedding-i deserialize edir (safe numpy format only).
        
        Security Note: pickle.loads() removed to prevent arbitrary code execution.
        Legacy pickle-format embeddings must be migrated using the migration script.
        
        Args:
            blob: Raw bytes from database
            expected_dim: Expected embedding dimension (default 256 for Gait)
            
        Returns:
            Numpy array of the embedding
            
        Raises:
            ValueError: If blob size doesn't match expected dimension
        """
        expected_size = expected_dim * 4  # float32 = 4 bytes
        
        if len(blob) != expected_size:
            raise ValueError(
                f"Invalid gait embedding blob size: {len(blob)} bytes. "
                f"Expected {expected_size} bytes for {expected_dim}-dim float32 embedding. "
                f"If this is legacy pickle data, run the migration script."
            )
        
        return np.frombuffer(blob, dtype=np.float32).copy()




# Singleton
_gait_engine: Optional[GaitEngine] = None


def get_gait_engine() -> GaitEngine:
    """Global GaitEngine instance qaytarır."""
    global _gait_engine
    if _gait_engine is None:
        models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        model_path = os.path.join(models_dir, 'gaitset.pth')
        _gait_engine = GaitEngine(model_path=model_path if os.path.exists(model_path) else None)
    return _gait_engine
