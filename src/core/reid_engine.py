"""
FacePro Re-ID Engine Module
Bədən/Geyim xüsusiyyətləri çıxarma və müqayisə.
EfficientNet-B0 feature extractor istifadə edir.
"""

import os
# Note: pickle removed for security - use numpy tobytes/frombuffer instead
from typing import Optional, List, Tuple
from dataclasses import dataclass

import cv2
import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger

logger = get_logger()

# Torch import (lazy loading - yalnız lazım olduqda)
_torch = None
_torchvision = None
_model = None


def _lazy_import_torch():
    """Torch-u lazy load edir (başlanğıc vaxtını azaldır)."""
    global _torch, _torchvision
    if _torch is None:
        try:
            import torch
            import torchvision
            _torch = torch
            _torchvision = torchvision
            logger.info(f"PyTorch loaded: {torch.__version__}, CUDA: {torch.cuda.is_available()}")
        except ImportError as e:
            logger.error(f"PyTorch import failed: {e}")
            raise
    return _torch, _torchvision


@dataclass
class ReIDMatch:
    """Re-ID uyğunluq nəticəsi."""
    user_id: int
    user_name: str
    confidence: float
    embedding_id: int


class ReIDEngine:
    """
    Person Re-Identification Engine.
    Bədən xüsusiyyətlərini çıxarır və müqayisə edir.
    """
    
    # Şəkil ölçüsü (EfficientNet-B0 girişi)
    INPUT_SIZE = (224, 224)
    
    # Embedding ölçüsü
    EMBEDDING_DIM = 1280  # EfficientNet-B0 output
    
    # Default confidence threshold
    DEFAULT_THRESHOLD = 0.75
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True):
        """
        Args:
            model_path: Model faylının yolu (None = pretrained)
            use_gpu: GPU istifadə etmək
        """
        self._model = None
        self._device = None
        self._transform = None
        self._model_path = model_path
        self._use_gpu = use_gpu
        self._threshold = self.DEFAULT_THRESHOLD
        
        logger.info("ReIDEngine created (lazy loading)")
    
    def _ensure_loaded(self):
        """Model-in yükləndiyini təmin edir (lazy loading)."""
        if self._model is not None:
            return
        
        torch, torchvision = _lazy_import_torch()
        
        # Device seçimi
        if self._use_gpu and torch.cuda.is_available():
            self._device = torch.device('cuda')
            logger.info("ReID using GPU")
        else:
            self._device = torch.device('cpu')
            logger.info("ReID using CPU")
        
        # Model yüklə
        try:
            if self._model_path and os.path.exists(self._model_path):
                # Custom model
                self._model = torch.load(self._model_path, map_location=self._device)
                logger.info(f"Custom ReID model loaded: {self._model_path}")
            else:
                # Pretrained EfficientNet-B0
                weights = torchvision.models.EfficientNet_B0_Weights.DEFAULT
                self._model = torchvision.models.efficientnet_b0(weights=weights)
                
                # Son classifier layer-i çıxar (yalnız feature extractor)
                self._model.classifier = torch.nn.Identity()
                
                logger.info("Pretrained EfficientNet-B0 loaded")
            
            self._model = self._model.to(self._device)
            self._model.eval()
            
        except Exception as e:
            logger.error(f"Failed to load ReID model: {e}")
            raise
        
        # Transform pipeline
        self._transform = torchvision.transforms.Compose([
            torchvision.transforms.ToPILImage(),
            torchvision.transforms.Resize(self.INPUT_SIZE),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def extract_embedding(self, person_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Şəxs şəklindən embedding çıxarır.
        
        Args:
            person_image: Şəxsin kəsilmiş şəkli (BGR, OpenCV format)
            
        Returns:
            Embedding vektoru (numpy array) və ya None
        """
        try:
            self._ensure_loaded()
            torch, _ = _lazy_import_torch()
            
            # BGR -> RGB
            rgb_image = cv2.cvtColor(person_image, cv2.COLOR_BGR2RGB)
            
            # Transform
            input_tensor = self._transform(rgb_image)
            input_batch = input_tensor.unsqueeze(0).to(self._device)
            
            # Feature extraction
            with torch.no_grad():
                embedding = self._model(input_batch)
            
            # Numpy-a çevir
            embedding_np = embedding.cpu().numpy().flatten()
            
            # L2 normalization
            norm = np.linalg.norm(embedding_np)
            if norm > 0:
                embedding_np = embedding_np / norm
            
            return embedding_np
            
        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None
    
    @staticmethod
    def cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        İki embedding arasında cosine similarity hesablayır.
        
        Args:
            embedding1: Birinci embedding
            embedding2: İkinci embedding
            
        Returns:
            Similarity score (0-1 arası, 1 = eyni)
        """
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(np.clip(similarity, 0, 1))
            
        except Exception:
            return 0.0
    
    def compare_embeddings(
        self, 
        query_embedding: np.ndarray, 
        stored_embeddings: List[Tuple[int, int, str, np.ndarray]],
        stored_matrix: Optional[np.ndarray] = None
    ) -> Optional[ReIDMatch]:
        """
        Query embedding-i saxlanılan embedding-lərlə müqayisə edir (Vectorized).
        
        Args:
            query_embedding: Sorğu embedding-i (1D array)
            stored_embeddings: Metadata list [(embedding_id, user_id, user_name, embedding), ...]
            stored_matrix: Opsional pre-built numpy matrix (N, D) sürət üçün.
                           Əgər None olarsa, stored_embeddings-dən on-the-fly yaradılır.
            
        Returns:
            Ən yaxşı uyğunluq (ReIDMatch) və ya None
        """
        if not stored_embeddings:
            return None

        try:
            # 1. Prepare Matrix
            if stored_matrix is not None:
                matrix = stored_matrix
            else:
                # On-the-fly vectorization (still faster than python loop for large N)
                # stored_embeddings[i][3] is vector
                matrix_list = [item[3] for item in stored_embeddings]
                matrix = np.vstack(matrix_list)

            # 2. Vectorized Cosine Similarity
            # Assuming query and database vectors are already L2 normalized!
            # If they are normalized, Cosine Similarity == Dot Product.
            # self.extract_embedding already normalizes outputs.
            
            # query_embedding shape: (D,) -> (1, D) for matrix mul? 
            # or just (D,) works with (N, D) -> (N,) result in numpy.
            
            scores = np.dot(matrix, query_embedding)
            
            # 3. Find Best Match
            best_idx = np.argmax(scores)
            best_score = float(scores[best_idx])
            
            if best_score >= self._threshold:
                # Get metadata from list
                emb_id, user_id, user_name, _ = stored_embeddings[best_idx]
                
                return ReIDMatch(
                    user_id=user_id,
                    user_name=user_name,
                    confidence=best_score,
                    embedding_id=emb_id
                )
            
            return None

        except Exception as e:
            logger.error(f"Vectorized comparison failed: {e}")
            return None
    
    def set_threshold(self, threshold: float):
        """Uyğunluq threshold-unu ayarla (0-1)."""
        self._threshold = max(0.0, min(1.0, threshold))
        logger.info(f"ReID threshold set to: {self._threshold}")
    
    @staticmethod
    def serialize_embedding(embedding: np.ndarray) -> bytes:
        """Embedding-i SQLite BLOB üçün serialize edir (safe numpy format)."""
        # Use numpy tobytes for security - no arbitrary code execution risk
        return embedding.astype(np.float32).tobytes()
    
    @staticmethod
    def deserialize_embedding(blob: bytes, expected_dim: int = 1280) -> np.ndarray:
        """
        BLOB-dan embedding-i deserialize edir (safe numpy format only).
        
        Security Note: pickle.loads() removed to prevent arbitrary code execution.
        Legacy pickle-format embeddings must be migrated using the migration script.
        
        Args:
            blob: Raw bytes from database
            expected_dim: Expected embedding dimension (default 1280 for EfficientNet-B0)
            
        Returns:
            Numpy array of the embedding
            
        Raises:
            ValueError: If blob size doesn't match expected dimension
        """
        expected_size = expected_dim * 4  # float32 = 4 bytes
        
        if len(blob) != expected_size:
            raise ValueError(
                f"Invalid embedding blob size: {len(blob)} bytes. "
                f"Expected {expected_size} bytes for {expected_dim}-dim float32 embedding. "
                f"If this is legacy pickle data, run the migration script."
            )
        
        return np.frombuffer(blob, dtype=np.float32).copy()


# Singleton instance
_reid_engine: Optional[ReIDEngine] = None


def get_reid_engine() -> ReIDEngine:
    """Global ReIDEngine instance qaytarır."""
    global _reid_engine
    if _reid_engine is None:
        models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'models'
        )
        model_path = os.path.join(models_dir, 'efficientnet_b0.pth')
        
        _reid_engine = ReIDEngine(
            model_path=model_path if os.path.exists(model_path) else None
        )
    return _reid_engine


if __name__ == "__main__":
    # Test
    print("Testing ReIDEngine...")
    
    engine = get_reid_engine()
    
    # Dummy test şəkli
    test_image = np.random.randint(0, 255, (300, 150, 3), dtype=np.uint8)
    
    print("Extracting embedding...")
    embedding = engine.extract_embedding(test_image)
    
    if embedding is not None:
        print(f"Embedding shape: {embedding.shape}")
        print(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
        
        # Self-similarity test
        sim = engine.cosine_similarity(embedding, embedding)
        print(f"Self-similarity: {sim:.4f}")
        
        # Serialize test
        serialized = ReIDEngine.serialize_embedding(embedding)
        deserialized = ReIDEngine.deserialize_embedding(serialized)
        print(f"Serialization test: {np.allclose(embedding, deserialized)}")
    else:
        print("Embedding extraction failed")
