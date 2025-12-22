"""
ReID Engine Unit Tests
Tests for Person Re-Identification functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch


class TestReIDEngineSingleton:
    """Test ReID Engine singleton pattern."""
    
    def test_import_reid_engine(self):
        """ReIDEngine modulu import olunmalı."""
        from src.core.reid_engine import get_reid_engine
        assert get_reid_engine is not None
    
    def test_singleton_pattern(self):
        """get_reid_engine() həmişə eyni instansı qaytarmalı."""
        from src.core.reid_engine import get_reid_engine
        
        engine1 = get_reid_engine()
        engine2 = get_reid_engine()
        
        assert engine1 is engine2
    
    def test_engine_not_none(self):
        """Engine None olmamalı."""
        from src.core.reid_engine import get_reid_engine
        engine = get_reid_engine()
        assert engine is not None


class TestReIDEngineExtraction:
    """Test embedding extraction."""
    
    @pytest.fixture
    def engine(self):
        from src.core.reid_engine import get_reid_engine
        return get_reid_engine()
    
    def test_extract_embedding_exists(self, engine):
        """extract_embedding metodu mövcud olmalı."""
        assert hasattr(engine, 'extract_embedding')
        assert callable(engine.extract_embedding)
    
    def test_extract_embedding_returns_array_or_none(self, engine, mock_person_crop):
        """extract_embedding() numpy array və ya None qaytarmalı."""
        result = engine.extract_embedding(mock_person_crop)
        # Model yüklü deyilsə None qaytara bilər
        assert result is None or isinstance(result, np.ndarray)
    
    def test_extract_embedding_none_input(self, engine):
        """None input ilə None qaytarmalı."""
        result = engine.extract_embedding(None)
        assert result is None
    
    def test_extract_embedding_empty_array(self, engine):
        """Boş array ilə None qaytarmalı."""
        empty_image = np.array([])
        result = engine.extract_embedding(empty_image)
        assert result is None


class TestReIDEngineSimilarity:
    """Test similarity calculations."""
    
    @pytest.fixture
    def engine(self):
        from src.core.reid_engine import get_reid_engine
        return get_reid_engine()
    
    def test_cosine_similarity_exists(self, engine):
        """cosine_similarity metodu mövcud olmalı."""
        assert hasattr(engine, 'cosine_similarity')
        assert callable(engine.cosine_similarity)
    
    def test_cosine_similarity_same_vector(self, engine):
        """Eyni vektorun özü ilə oxşarlığı 1.0 olmalı."""
        vec = np.random.rand(1280).astype(np.float32)
        similarity = engine.cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0, abs=0.01)
    
    def test_cosine_similarity_orthogonal(self, engine):
        """Ortogonal vektorların oxşarlığı 0 olmalı."""
        vec1 = np.zeros(1280, dtype=np.float32)
        vec1[0] = 1.0
        vec2 = np.zeros(1280, dtype=np.float32)
        vec2[1] = 1.0
        
        similarity = engine.cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0, abs=0.01)
    
    def test_cosine_similarity_range(self, engine):
        """Cosine similarity [-1, 1] aralığında olmalı."""
        vec1 = np.random.rand(1280).astype(np.float32)
        vec2 = np.random.rand(1280).astype(np.float32)
        
        similarity = engine.cosine_similarity(vec1, vec2)
        assert -1.0 <= similarity <= 1.0


class TestReIDEngineSerialization:
    """Test embedding serialization."""
    
    @pytest.fixture
    def engine(self):
        from src.core.reid_engine import get_reid_engine
        return get_reid_engine()
    
    def test_serialize_exists(self, engine):
        """serialize_embedding metodu mövcud olmalı."""
        assert hasattr(engine, 'serialize_embedding')
    
    def test_deserialize_exists(self, engine):
        """deserialize_embedding metodu mövcud olmalı."""
        assert hasattr(engine, 'deserialize_embedding')
    
    def test_serialize_deserialize_roundtrip(self, engine):
        """Serialization/deserialization eyni dəyəri verməli."""
        original = np.random.rand(1280).astype(np.float32)
        
        serialized = engine.serialize_embedding(original)
        assert isinstance(serialized, bytes)
        
        deserialized = engine.deserialize_embedding(serialized)
        assert isinstance(deserialized, np.ndarray)
        
        assert np.allclose(original, deserialized)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
