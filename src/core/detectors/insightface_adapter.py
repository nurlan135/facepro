"""
FacePro InsightFace Adapter
---------------------------
InsightFace (ONNX) kitabxanasını əhatə edən adapter sinfi.
Dlib-dən ~6x daha sürətli üz tanıma təmin edir.

Note: InsightFace 512d vektor istehsal edir (dlib-in 128d əksinə).
"""

import os
from typing import Optional, List, Tuple, Dict
import numpy as np
import cv2

from src.utils.logger import get_logger

logger = get_logger()


class InsightFaceAdapter:
    """
    InsightFace (ArcFace) based face recognition adapter.
    
    Features:
        - CPU/GPU auto-detection
        - Buffalo_L model pack (default)
        - 512-dimensional face embeddings
        - Integrated face detection + encoding
    """
    
    # Model configuration
    MODEL_NAME = 'buffalo_l'  # 'buffalo_s' for smaller/faster model
    DET_SIZE = (640, 640)
    EMBEDDING_DIM = 512
    
    def __init__(self, provider: str = 'auto'):
        """
        Args:
            provider: 'CPUExecutionProvider', 'CUDAExecutionProvider', or 'auto'
        """
        self._app = None
        self._provider = provider
        self._initialized = False
        logger.info(f"InsightFaceAdapter created (lazy loading, provider={provider})")
    
    def _initialize(self):
        """Lazy initialization - loads models on first use."""
        if self._initialized:
            return
        
        try:
            from insightface.app import FaceAnalysis
            
            # Determine provider
            if self._provider == 'auto':
                try:
                    import onnxruntime as ort
                    available = ort.get_available_providers()
                    if 'CUDAExecutionProvider' in available:
                        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
                        logger.info("InsightFace: Using CUDA GPU acceleration")
                    else:
                        providers = ['CPUExecutionProvider']
                        logger.info("InsightFace: Using CPU (no CUDA detected)")
                except Exception:
                    providers = ['CPUExecutionProvider']
            else:
                providers = [self._provider]
            
            # Initialize FaceAnalysis
            self._app = FaceAnalysis(
                name=self.MODEL_NAME,
                providers=providers
            )
            self._app.prepare(ctx_id=0, det_size=self.DET_SIZE)
            
            self._initialized = True
            logger.info(f"InsightFace initialized with model '{self.MODEL_NAME}'")
            
        except ImportError as e:
            logger.error(f"InsightFace not installed: {e}")
            raise RuntimeError("InsightFace not installed. Run: pip install insightface onnxruntime")
        except Exception as e:
            logger.error(f"InsightFace initialization failed: {e}")
            raise
    
    def detect_faces(self, img_bgr: np.ndarray) -> List[Dict]:
        """
        Şəkildə bütün üzləri aşkarlayır.
        
        Args:
            img_bgr: BGR formatında şəkil (OpenCV format)
            
        Returns:
            List of face dicts with keys:
                - bbox: (x1, y1, x2, y2)
                - embedding: 512d numpy array
                - det_score: detection confidence
                - gender: 'M' or 'F'
                - age: estimated age
        """
        self._initialize()
        
        if img_bgr is None or img_bgr.size == 0:
            return []
        
        try:
            faces = self._app.get(img_bgr)
            
            result = []
            for face in faces:
                face_dict = {
                    'bbox': tuple(map(int, face.bbox)),
                    'embedding': face.embedding,
                    'det_score': float(face.det_score),
                }
                
                # Optional: gender and age if available
                if hasattr(face, 'gender'):
                    face_dict['gender'] = 'M' if face.gender == 1 else 'F'
                if hasattr(face, 'age'):
                    face_dict['age'] = int(face.age)
                
                result.append(face_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"InsightFace detection error: {e}")
            return []
    
    def get_embedding(self, img_bgr: np.ndarray) -> Optional[np.ndarray]:
        """
        Şəkildə ən böyük üzün embedding-ini qaytarır.
        
        Args:
            img_bgr: BGR formatında şəkil
            
        Returns:
            512d numpy array or None if no face found
        """
        faces = self.detect_faces(img_bgr)
        
        if not faces:
            return None
        
        # Get largest face by area
        largest = max(faces, key=lambda f: 
            (f['bbox'][2] - f['bbox'][0]) * (f['bbox'][3] - f['bbox'][1])
        )
        
        return largest['embedding']
    
    def get_all_embeddings(self, img_bgr: np.ndarray) -> List[np.ndarray]:
        """
        Şəkildəki bütün üzlərin embedding-lərini qaytarır.
        
        Args:
            img_bgr: BGR formatında şəkil
            
        Returns:
            List of 512d numpy arrays
        """
        faces = self.detect_faces(img_bgr)
        return [f['embedding'] for f in faces]
    
    def compare_embeddings(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        İki üz embedding-i arasındakı oxşarlığı hesablayır.
        
        Args:
            embedding1: First face embedding (512d)
            embedding2: Second face embedding (512d)
            
        Returns:
            Cosine similarity score (0.0 to 1.0, higher = more similar)
        """
        # Normalize embeddings
        norm1 = embedding1 / np.linalg.norm(embedding1)
        norm2 = embedding2 / np.linalg.norm(embedding2)
        
        # Cosine similarity
        similarity = np.dot(norm1, norm2)
        
        # Clip to valid range
        return float(np.clip(similarity, 0.0, 1.0))
    
    def find_best_match(
        self,
        unknown_embedding: np.ndarray,
        known_embeddings: Dict[str, List[np.ndarray]],
        threshold: float = 0.4
    ) -> Tuple[Optional[str], float]:
        """
        Naməlum üzü tanınmış üzlər arasında axtarır.
        
        Args:
            unknown_embedding: Üz vektoru (512d)
            known_embeddings: {name: [embedding1, embedding2, ...]}
            threshold: Minimum oxşarlıq (InsightFace üçün 0.4 tövsiyə olunur)
            
        Returns:
            (matched_name, confidence) or (None, 0.0)
        """
        best_name = None
        best_score = 0.0
        
        for name, embeddings_list in known_embeddings.items():
            for known_emb in embeddings_list:
                score = self.compare_embeddings(unknown_embedding, known_emb)
                if score > best_score:
                    best_score = score
                    best_name = name
        
        if best_score >= threshold:
            return best_name, best_score
        
        return None, 0.0

    @property
    def embedding_dim(self) -> int:
        """Embedding dimensiyası (InsightFace = 512)."""
        return self.EMBEDDING_DIM
    
    @property
    def is_initialized(self) -> bool:
        """Model yüklənib-yüklənmədiyini göstərir."""
        return self._initialized
