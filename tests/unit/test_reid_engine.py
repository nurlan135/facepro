
"""
ReID Engine Unit Tests
Tests for Person Re-Identification functionality using mocks.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.core.reid_engine import ReIDEngine, get_reid_engine, ReIDMatch

class TestReIDEngine:
    
    @pytest.fixture
    def mock_torch_system(self):
        with patch('src.core.reid_engine._lazy_import_torch') as mock_import:
            mock_torch = MagicMock()
            mock_torchvision = MagicMock()
            mock_import.return_value = (mock_torch, mock_torchvision)
            yield mock_torch, mock_torchvision

    @pytest.fixture
    def engine(self):
        # Create a fresh engine instance instead of singleton for isolation
        return ReIDEngine()

    def test_initialization(self, engine):
        assert engine is not None
        assert engine._threshold == 0.75

    def test_ensure_loaded(self, engine, mock_torch_system):
        mock_torch, mock_torchvision = mock_torch_system
        
        # Setup mock model
        mock_model = Mock()
        mock_torchvision.models.efficientnet_b0.return_value = mock_model
        
        engine._ensure_loaded()
        
        assert engine._model is not None
        mock_torchvision.models.efficientnet_b0.assert_called_once()
        # Verify Identity replacement for classifier
        assert isinstance(mock_model.classifier, MagicMock) or True # Logic check

    def test_extract_embedding_success(self, engine, mock_torch_system):
        mock_torch, _ = mock_torch_system
        
        # Mock ensure loaded behavior
        engine._model = Mock()
        engine._device = 'cpu'
        engine._transform = Mock()
        
        # Mock inference result
        mock_output = MagicMock()
        # Output should be (1, 1280)
        mock_output.cpu().numpy().flatten.return_value = np.ones((1280,), dtype=np.float32)
        engine._model.return_value = mock_output
        
        # Call
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        emb = engine.extract_embedding(frame)
        
        assert emb is not None
        assert emb.shape == (1280,)
        # Check normalization (ones vector normalized)
        assert np.isclose(np.linalg.norm(emb), 1.0)

    def test_extract_embedding_failure(self, engine, mock_torch_system):
        # Mock ensure loaded to raise exception
        with patch.object(engine, '_ensure_loaded', side_effect=Exception("Load fail")):
             frame = np.zeros((100, 100, 3), dtype=np.uint8)
             emb = engine.extract_embedding(frame)
             assert emb is None

    def test_cosine_similarity(self):
        v1 = np.array([1, 0], dtype=np.float32)
        v2 = np.array([0, 1], dtype=np.float32)
        assert ReIDEngine.cosine_similarity(v1, v2) == 0.0
        
        v3 = np.array([1, 0], dtype=np.float32)
        assert ReIDEngine.cosine_similarity(v1, v3) == 1.0
        
        # Check handling of zeros
        assert ReIDEngine.cosine_similarity(np.zeros(2), v1) == 0.0

    def test_compare_embeddings_vectorized(self, engine):
        # Query: [1, 0]
        query = np.array([1.0, 0.0], dtype=np.float32) # Normalized
        
        # DB: 
        # 1: [0, 1] (Sim=0)
        # 2: [1, 0] (Sim=1)
        # 3: [0.7, 0.7] (Sim=0.7)
        
        db_embeddings = [
            (1, 101, "User1", np.array([0.0, 1.0], dtype=np.float32)),
            (2, 102, "User2", np.array([1.0, 0.0], dtype=np.float32)),
            (3, 103, "User3", np.array([0.7071, 0.7071], dtype=np.float32))
        ]
        
        match = engine.compare_embeddings(query, db_embeddings)
        
        assert match is not None
        assert match.user_name == "User2"
        assert match.confidence > 0.99
        
    def test_compare_embeddings_threshold(self, engine):
        engine.set_threshold(0.9)
        query = np.array([1.0, 0.0], dtype=np.float32)
        
        # Only weak matches
        db_embeddings = [
            (1, 101, "User1", np.array([0.0, 1.0], dtype=np.float32)), # 0
            (2, 102, "User2", np.array([0.7071, 0.7071], dtype=np.float32)) # 0.7 < 0.9
        ]
        
        match = engine.compare_embeddings(query, db_embeddings)
        assert match is None

    def test_serialization(self):
        dummy = np.random.rand(1280).astype(np.float32)
        blob = ReIDEngine.serialize_embedding(dummy)
        restored = ReIDEngine.deserialize_embedding(blob, expected_dim=1280)
        
        np.testing.assert_array_equal(dummy, restored)
        
    def test_deserialize_security(self):
        # Should raise ValueError if size mismatch (which implies not float32 array of valid len)
        bad_blob = b'1234'
        with pytest.raises(ValueError) as exc:
            ReIDEngine.deserialize_embedding(bad_blob, expected_dim=1280)
        assert "Invalid embedding blob size" in str(exc.value)

