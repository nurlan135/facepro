"""
FacePro Gait Recognition Engine
Yeriş xüsusiyyətləri çıxarma və müqayisə.
Silhouette-based gait recognition using CNN feature extractor.
"""

import os
import pickle
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
                self._model = torch.load(self._model_path, map_location=self._device)
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
                embeddings = []
                for i in range(self.SEQUENCE_LENGTH):
                    frame_tensor = silhouette_tensor[i:i+1]
                    emb = self._model(frame_tensor)
                    embeddings.append(emb)
                avg_embedding = torch.mean(torch.stack(embeddings), dim=0)
            
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
    
    def compare_embeddings(self, query_embedding: np.ndarray, 
                          stored_embeddings: List[Tuple[int, int, str, np.ndarray]]) -> Optional[GaitMatch]:
        """Query embedding-i saxlanılan embedding-lərlə müqayisə edir."""
        best_match = None
        best_score = 0.0
        
        for emb_id, user_id, user_name, stored_emb in stored_embeddings:
            score = self.cosine_similarity(query_embedding, stored_emb)
            
            if score > best_score and score >= self._threshold:
                best_score = score
                best_match = GaitMatch(user_id=user_id, user_name=user_name, 
                                       confidence=score, embedding_id=emb_id)
        
        return best_match
    
    def set_threshold(self, threshold: float):
        self._threshold = max(0.0, min(1.0, threshold))
    
    def get_threshold(self) -> float:
        return self._threshold
    
    @staticmethod
    def serialize_embedding(embedding: np.ndarray) -> bytes:
        return pickle.dumps(embedding)
    
    @staticmethod
    def deserialize_embedding(blob: bytes) -> np.ndarray:
        return pickle.loads(blob)

    def save_embedding(self, user_id: int, embedding: np.ndarray, 
                      confidence: float = 1.0, db_path: Optional[str] = None) -> Optional[int]:
        """Gait embedding-i verilənlər bazasına saxlayır."""
        import sqlite3
        from src.utils.helpers import get_db_path
        
        if db_path is None:
            db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            embedding_blob = self.serialize_embedding(embedding)
            
            cursor.execute("SELECT COUNT(*) FROM gait_embeddings WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            
            MAX_EMBEDDINGS_PER_USER = 10
            if count >= MAX_EMBEDDINGS_PER_USER:
                delete_count = count - MAX_EMBEDDINGS_PER_USER + 1
                cursor.execute("""
                    DELETE FROM gait_embeddings WHERE id IN (
                        SELECT id FROM gait_embeddings WHERE user_id = ? 
                        ORDER BY captured_at ASC LIMIT ?
                    )
                """, (user_id, delete_count))
            
            cursor.execute(
                "INSERT INTO gait_embeddings (user_id, embedding, confidence) VALUES (?, ?, ?)",
                (user_id, embedding_blob, confidence)
            )
            
            embedding_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Gait embedding saved: user_id={user_id}, id={embedding_id}")
            return embedding_id
        except Exception as e:
            logger.error(f"Failed to save gait embedding: {e}")
            return None
    
    def load_embeddings(self, db_path: Optional[str] = None) -> List[Tuple[int, int, str, np.ndarray]]:
        """Bütün gait embedding-ləri verilənlər bazasından yükləyir."""
        import sqlite3
        from src.utils.helpers import get_db_path
        
        if db_path is None:
            db_path = get_db_path()
        
        embeddings = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ge.id, ge.user_id, u.name, ge.embedding
                FROM gait_embeddings ge JOIN users u ON ge.user_id = u.id
                ORDER BY ge.user_id, ge.captured_at DESC
            """)
            
            for row in cursor.fetchall():
                emb_id, user_id, user_name, embedding_blob = row
                try:
                    embedding = self.deserialize_embedding(embedding_blob)
                    embeddings.append((emb_id, user_id, user_name, embedding))
                except Exception as e:
                    logger.warning(f"Failed to deserialize embedding {emb_id}: {e}")
            
            conn.close()
            logger.info(f"Loaded {len(embeddings)} gait embeddings from database")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to load gait embeddings: {e}")
            return []
    
    def get_user_embedding_count(self, user_id: int, db_path: Optional[str] = None) -> int:
        """İstifadəçi üçün embedding sayını qaytarır."""
        import sqlite3
        from src.utils.helpers import get_db_path
        
        if db_path is None:
            db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM gait_embeddings WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Failed to get embedding count: {e}")
            return 0


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
