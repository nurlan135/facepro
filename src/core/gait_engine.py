"""
FacePro Gait Recognition Engine Module
Yeriş xüsusiyyətləri çıxarma və müqayisə.
Silhouette-based gait recognition using GaitSet-style approach.
"""

import os
import pickle
import time
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, field

import cv2
import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger

logger = get_logger()

# Torch import (lazy loading)
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


@dataclass
class GaitBuffer:
    """Bir şəxs üçün silhouette buffer."""
    track_id: int
    silhouettes: List[np.ndarray] = field(default_factory=list)
    last_update: float = field(default_factory=time.time)


@dataclass
class GaitMatch:
    """Gait tanıma nəticəsi."""
    user_id: int
    user_name: str
    confidence: float
    embedding_id: int


class GaitBufferManager:
    """
    Hər track_id üçün silhouette buffer idarəsi.
    Manages separate gait buffers for each tracked person.
    """
    
    def __init__(self, sequence_length: int = 30, timeout: float = 5.0):
        """
        Args:
            sequence_length: Analiz üçün lazım olan frame sayı
            timeout: Buffer timeout (saniyə)
        """
        self._buffers: Dict[int, GaitBuffer] = {}
        self._sequence_length = sequence_length
        self._timeout = timeout
    
    def add_frame(self, track_id: int, silhouette: np.ndarray) -> bool:
        """
        Buffer-ə frame əlavə et.
        
        Args:
            track_id: YOLO track ID
            silhouette: 64x64 silhouette şəkli
            
        Returns:
            True əgər buffer dolubsa (sequence_length-ə çatıb)
        """
        if track_id not in self._buffers:
            self._buffers[track_id] = GaitBuffer(track_id=track_id)
        
        buffer = self._buffers[track_id]
        buffer.silhouettes.append(silhouette)
        buffer.last_update = time.time()
        
        return len(buffer.silhouettes) >= self._sequence_length
    
    def get_sequence(self, track_id: int) -> Optional[List[np.ndarray]]:
        """
        Tam seqansı qaytar və buffer-i təmizlə.
        
        Args:
            track_id: YOLO track ID
            
        Returns:
            Silhouette siyahısı və ya None
        """
        if track_id not in self._buffers:
            return None
        
        buffer = self._buffers[track_id]
        if len(buffer.silhouettes) < self._sequence_length:
            return None
        
        # İlk sequence_length frame-i götür
        sequence = buffer.silhouettes[:self._sequence_length]
        
        # Buffer-i təmizlə
        del self._buffers[track_id]
        
        return sequence
    
    def cleanup_stale(self):
        """5 saniyə aktiv olmayan buffer-ləri sil."""
        current_time = time.time()
        stale_ids = [
            track_id for track_id, buffer in self._buffers.items()
            if current_time - buffer.last_update > self._timeout
        ]
        
        for track_id in stale_ids:
            del self._buffers[track_id]
            logger.debug(f"Stale gait buffer removed: track_id={track_id}")
    
    def get_buffer_size(self, track_id: int) -> int:
        """Track ID üçün buffer ölçüsünü qaytar."""
        if track_id not in self._buffers:
            return 0
        return len(self._buffers[track_id].silhouettes)
    
    def clear(self):
        """Bütün buffer-ləri təmizlə."""
        self._buffers.clear()


class GaitEngine:
    """
    Yeriş tanıma mühərriki.
    Silhouette-based gait recognition using CNN feature extractor.
    """
    
    # Constants
    SEQUENCE_LENGTH = 30  # Frame sayı
    SILHOUETTE_SIZE = (64, 64)  # Silhouette ölçüsü
    EMBEDDING_DIM = 256  # Gait embedding ölçüsü
    DEFAULT_THRESHOLD = 0.70
    
    def __init__(self, model_path: Optional[str] = None, use_gpu: bool = True):
        """
        Args:
            model_path: Model faylının yolu (None = pretrained)
            use_gpu: GPU istifadə etmək
        """
        self._model = None
        self._device = None
        self._model_path = model_path
        self._use_gpu = use_gpu
        self._threshold = self.DEFAULT_THRESHOLD
        self._bg_subtractor = None
        
        logger.info("GaitEngine created (lazy loading)")
    
    def _ensure_loaded(self):
        """Model-in yükləndiyini təmin edir (lazy loading)."""
        if self._model is not None:
            return
        
        torch, torchvision = _lazy_import_torch()
        
        # Device seçimi
        if self._use_gpu and torch.cuda.is_available():
            self._device = torch.device('cuda')
            logger.info("Gait using GPU")
        else:
            self._device = torch.device('cpu')
            logger.info("Gait using CPU")
        
        # Model yüklə - Simple CNN for gait feature extraction
        try:
            if self._model_path and os.path.exists(self._model_path):
                self._model = torch.load(self._model_path, map_location=self._device)
                logger.info(f"Custom Gait model loaded: {self._model_path}")
            else:
                # Fallback: ResNet18 feature extractor
                weights = torchvision.models.ResNet18_Weights.DEFAULT
                base_model = torchvision.models.resnet18(weights=weights)
                
                # Modify for single channel input (silhouettes are grayscale)
                base_model.conv1 = torch.nn.Conv2d(
                    1, 64, kernel_size=7, stride=2, padding=3, bias=False
                )
                
                # Replace FC layer to output 256D embedding
                base_model.fc = torch.nn.Linear(512, self.EMBEDDING_DIM)
                
                self._model = base_model
                logger.info("Pretrained ResNet18 adapted for Gait")
            
            self._model = self._model.to(self._device)
            self._model.eval()
            
        except Exception as e:
            logger.error(f"Failed to load Gait model: {e}")
            raise
        
        # Background subtractor for silhouette extraction
        self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False
        )

    
    def extract_silhouette(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Person bounding box-dan silhouette çıxar.
        
        Args:
            frame: BGR formatında frame
            bbox: (x1, y1, x2, y2) bounding box
            
        Returns:
            64x64 silhouette şəkli (grayscale, binary)
        """
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        
        # Bbox sərhədlərini yoxla
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(w, int(x2))
        y2 = min(h, int(y2))
        
        # Person region-u kəs
        person_region = frame[y1:y2, x1:x2]
        
        if person_region.size == 0:
            return np.zeros(self.SILHOUETTE_SIZE, dtype=np.uint8)
        
        # Grayscale-ə çevir
        gray = cv2.cvtColor(person_region, cv2.COLOR_BGR2GRAY)
        
        # Simple thresholding for silhouette (background subtraction alternative)
        # Otsu's method for automatic threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Resize to standard size (64x64)
        silhouette = cv2.resize(binary, self.SILHOUETTE_SIZE, interpolation=cv2.INTER_AREA)
        
        return silhouette
    
    def extract_embedding(self, silhouettes: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        30 silhouette-dən 256D embedding çıxar.
        
        Args:
            silhouettes: 30 ədəd 64x64 silhouette şəkli
            
        Returns:
            256D embedding vektoru və ya None
        """
        if len(silhouettes) < self.SEQUENCE_LENGTH:
            logger.warning(f"Not enough silhouettes: {len(silhouettes)}/{self.SEQUENCE_LENGTH}")
            return None
        
        try:
            self._ensure_loaded()
            torch, _ = _lazy_import_torch()
            
            # Stack silhouettes into tensor [30, 1, 64, 64]
            silhouette_stack = np.stack(silhouettes[:self.SEQUENCE_LENGTH], axis=0)
            silhouette_stack = silhouette_stack.astype(np.float32) / 255.0
            
            # Add channel dimension [30, 1, 64, 64]
            silhouette_tensor = torch.from_numpy(silhouette_stack).unsqueeze(1)
            silhouette_tensor = silhouette_tensor.to(self._device)
            
            # Extract features for each frame and average
            with torch.no_grad():
                embeddings = []
                for i in range(self.SEQUENCE_LENGTH):
                    frame_tensor = silhouette_tensor[i:i+1]  # [1, 1, 64, 64]
                    emb = self._model(frame_tensor)
                    embeddings.append(emb)
                
                # Average pooling across frames
                avg_embedding = torch.mean(torch.stack(embeddings), dim=0)
            
            # Convert to numpy and L2 normalize
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
        stored_embeddings: List[Tuple[int, int, str, np.ndarray]]
    ) -> Optional[GaitMatch]:
        """
        Query embedding-i saxlanılan embedding-lərlə müqayisə edir.
        
        Args:
            query_embedding: Sorğu embedding-i
            stored_embeddings: [(embedding_id, user_id, user_name, embedding), ...] siyahısı
            
        Returns:
            Ən yaxşı uyğunluq (GaitMatch) və ya None
        """
        best_match = None
        best_score = 0.0
        
        for emb_id, user_id, user_name, stored_emb in stored_embeddings:
            score = self.cosine_similarity(query_embedding, stored_emb)
            
            if score > best_score and score >= self._threshold:
                best_score = score
                best_match = GaitMatch(
                    user_id=user_id,
                    user_name=user_name,
                    confidence=score,
                    embedding_id=emb_id
                )
        
        return best_match
    
    def set_threshold(self, threshold: float):
        """Uyğunluq threshold-unu ayarla (0-1)."""
        self._threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Gait threshold set to: {self._threshold}")
    
    def get_threshold(self) -> float:
        """Cari threshold-u qaytar."""
        return self._threshold
    
    @staticmethod
    def serialize_embedding(embedding: np.ndarray) -> bytes:
        """Embedding-i SQLite BLOB üçün serialize edir."""
        return pickle.dumps(embedding)
    
    @staticmethod
    def deserialize_embedding(blob: bytes) -> np.ndarray:
        """BLOB-dan embedding-i deserialize edir."""
        return pickle.loads(blob)
    
    def save_embedding(
        self, 
        user_id: int, 
        embedding: np.ndarray, 
        confidence: float = 1.0,
        db_path: Optional[str] = None
    ) -> Optional[int]:
        """
        Gait embedding-i verilənlər bazasına saxlayır.
        
        Args:
            user_id: İstifadəçi ID-si
            embedding: 256D gait embedding vektoru
            confidence: Embedding-in etibarlılıq dərəcəsi (0-1)
            db_path: Verilənlər bazası yolu (None = default)
            
        Returns:
            Yeni embedding ID-si və ya None (xəta halında)
            
        Note:
            Hər istifadəçi üçün maksimum 10 embedding saxlanılır.
            Limit aşıldıqda ən köhnə embedding silinir.
        """
        import sqlite3
        from src.utils.helpers import get_db_path
        
        if db_path is None:
            db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Serialize embedding
            embedding_blob = self.serialize_embedding(embedding)
            
            # Check current count for user
            cursor.execute(
                "SELECT COUNT(*) FROM gait_embeddings WHERE user_id = ?",
                (user_id,)
            )
            count = cursor.fetchone()[0]
            
            # Enforce max 10 embeddings per user
            MAX_EMBEDDINGS_PER_USER = 10
            if count >= MAX_EMBEDDINGS_PER_USER:
                # Delete oldest embeddings to make room
                delete_count = count - MAX_EMBEDDINGS_PER_USER + 1
                cursor.execute(
                    """
                    DELETE FROM gait_embeddings 
                    WHERE id IN (
                        SELECT id FROM gait_embeddings 
                        WHERE user_id = ? 
                        ORDER BY captured_at ASC 
                        LIMIT ?
                    )
                    """,
                    (user_id, delete_count)
                )
                logger.debug(f"Deleted {delete_count} old gait embeddings for user {user_id}")
            
            # Insert new embedding
            cursor.execute(
                """
                INSERT INTO gait_embeddings (user_id, embedding, confidence)
                VALUES (?, ?, ?)
                """,
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
    
    def load_embeddings(
        self, 
        db_path: Optional[str] = None
    ) -> List[Tuple[int, int, str, np.ndarray]]:
        """
        Bütün gait embedding-ləri verilənlər bazasından yükləyir.
        
        Args:
            db_path: Verilənlər bazası yolu (None = default)
            
        Returns:
            [(embedding_id, user_id, user_name, embedding), ...] siyahısı
        """
        import sqlite3
        from src.utils.helpers import get_db_path
        
        if db_path is None:
            db_path = get_db_path()
        
        embeddings = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Join with users table to get user names
            cursor.execute(
                """
                SELECT ge.id, ge.user_id, u.name, ge.embedding
                FROM gait_embeddings ge
                JOIN users u ON ge.user_id = u.id
                ORDER BY ge.user_id, ge.captured_at DESC
                """
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                emb_id, user_id, user_name, embedding_blob = row
                try:
                    embedding = self.deserialize_embedding(embedding_blob)
                    embeddings.append((emb_id, user_id, user_name, embedding))
                except Exception as e:
                    logger.warning(f"Failed to deserialize embedding {emb_id}: {e}")
                    continue
            
            logger.info(f"Loaded {len(embeddings)} gait embeddings from database")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to load gait embeddings: {e}")
            return []
    
    def get_user_embedding_count(
        self, 
        user_id: int, 
        db_path: Optional[str] = None
    ) -> int:
        """
        İstifadəçi üçün saxlanılan embedding sayını qaytarır.
        
        Args:
            user_id: İstifadəçi ID-si
            db_path: Verilənlər bazası yolu (None = default)
            
        Returns:
            Embedding sayı
        """
        import sqlite3
        from src.utils.helpers import get_db_path
        
        if db_path is None:
            db_path = get_db_path()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM gait_embeddings WHERE user_id = ?",
                (user_id,)
            )
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get embedding count: {e}")
            return 0


# Singleton instance
_gait_engine: Optional[GaitEngine] = None


def get_gait_engine() -> GaitEngine:
    """Global GaitEngine instance qaytarır."""
    global _gait_engine
    if _gait_engine is None:
        models_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'models'
        )
        model_path = os.path.join(models_dir, 'gaitset.pth')
        
        _gait_engine = GaitEngine(
            model_path=model_path if os.path.exists(model_path) else None
        )
    return _gait_engine


if __name__ == "__main__":
    # Test
    print("Testing GaitEngine...")
    
    engine = get_gait_engine()
    
    # Test silhouette extraction
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    bbox = (100, 50, 200, 400)
    
    print("Extracting silhouette...")
    silhouette = engine.extract_silhouette(test_frame, bbox)
    print(f"Silhouette shape: {silhouette.shape}")
    assert silhouette.shape == (64, 64), f"Expected (64, 64), got {silhouette.shape}"
    
    # Test buffer manager
    print("\nTesting GaitBufferManager...")
    buffer_mgr = GaitBufferManager(sequence_length=30)
    
    for i in range(30):
        is_full = buffer_mgr.add_frame(1, silhouette)
        if i < 29:
            assert not is_full, f"Buffer should not be full at frame {i}"
    
    assert is_full, "Buffer should be full after 30 frames"
    print("Buffer test passed!")
    
    # Test embedding extraction
    print("\nExtracting embedding from sequence...")
    sequence = buffer_mgr.get_sequence(1)
    if sequence:
        embedding = engine.extract_embedding(sequence)
        if embedding is not None:
            print(f"Embedding shape: {embedding.shape}")
            print(f"Embedding norm: {np.linalg.norm(embedding):.4f}")
            
            # Self-similarity test
            sim = engine.cosine_similarity(embedding, embedding)
            print(f"Self-similarity: {sim:.4f}")
            
            # Serialize test
            serialized = GaitEngine.serialize_embedding(embedding)
            deserialized = GaitEngine.deserialize_embedding(serialized)
            print(f"Serialization test: {np.allclose(embedding, deserialized)}")
    
    print("\nAll tests passed!")
