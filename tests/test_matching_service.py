"""
Unit tests for MatchingService.

Tests cover:
- Initialization with default and injected dependencies
- Data loading (Re-ID, Gait)
- Lazy matrix rebuild optimization
- Vector matching functionality
- Dimension validation
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch


class TestMatchingServiceInit:
    """Tests for MatchingService initialization."""
    
    def test_init_with_default_engines(self):
        """Should initialize with default singleton engines."""
        with patch('src.core.services.matching_service.get_reid_engine') as mock_reid, \
             patch('src.core.services.matching_service.get_gait_engine') as mock_gait:
            
            mock_reid.return_value = Mock()
            mock_gait.return_value = Mock()
            
            from src.core.services.matching_service import MatchingService
            service = MatchingService()
            
            mock_reid.assert_called_once()
            mock_gait.assert_called_once()
            assert service._reid_engine is not None
            assert service._gait_engine is not None
    
    def test_init_with_injected_engines(self):
        """Should use injected engines instead of singletons."""
        mock_reid = Mock()
        mock_gait = Mock()
        
        with patch('src.core.services.matching_service.get_reid_engine') as patched_reid, \
             patch('src.core.services.matching_service.get_gait_engine') as patched_gait:
            
            from src.core.services.matching_service import MatchingService
            service = MatchingService(reid_engine=mock_reid, gait_engine=mock_gait)
            
            # Singletons should NOT be called when engines are injected
            patched_reid.assert_not_called()
            patched_gait.assert_not_called()
            
            assert service._reid_engine is mock_reid
            assert service._gait_engine is mock_gait
    
    def test_init_empty_caches(self):
        """Should initialize with empty caches and matrices."""
        with patch('src.core.services.matching_service.get_reid_engine'), \
             patch('src.core.services.matching_service.get_gait_engine'):
            
            from src.core.services.matching_service import MatchingService
            service = MatchingService()
            
            assert service._reid_cache == []
            assert service._gait_cache == []
            assert service._reid_matrix is None
            assert service._gait_matrix is None
            assert service._reid_matrix_dirty is False
            assert service._gait_matrix_dirty is False


class TestMatchingServiceLoadData:
    """Tests for data loading functionality."""
    
    @pytest.fixture
    def service(self):
        """Create a MatchingService with mocked engines."""
        mock_reid = Mock()
        mock_reid.embedding_size = 1280
        mock_gait = Mock()
        mock_gait.embedding_size = 256
        
        with patch('src.core.services.matching_service.get_reid_engine', return_value=mock_reid), \
             patch('src.core.services.matching_service.get_gait_engine', return_value=mock_gait):
            from src.core.services.matching_service import MatchingService
            return MatchingService()
    
    def test_load_reid_data_builds_matrix(self, service):
        """Should build numpy matrix from loaded embeddings."""
        embeddings = [
            (1, 101, "User1", np.random.randn(1280).astype(np.float32)),
            (2, 102, "User2", np.random.randn(1280).astype(np.float32)),
        ]
        
        service.load_reid_data(embeddings)
        
        assert len(service._reid_cache) == 2
        assert service._reid_matrix is not None
        assert service._reid_matrix.shape == (2, 1280)
    
    def test_load_reid_data_rejects_wrong_dimension(self, service):
        """Should skip embeddings with wrong dimensions."""
        embeddings = [
            (1, 101, "User1", np.random.randn(1280).astype(np.float32)),  # Valid
            (2, 102, "User2", np.random.randn(512).astype(np.float32)),   # Invalid
            (3, 103, "User3", np.random.randn(1280).astype(np.float32)),  # Valid
        ]
        
        service.load_reid_data(embeddings)
        
        assert len(service._reid_cache) == 2  # Only 2 valid
        assert service._reid_matrix.shape == (2, 1280)
    
    def test_load_gait_data_builds_matrix(self, service):
        """Should build numpy matrix from loaded gait embeddings."""
        embeddings = [
            (1, 101, "User1", np.random.randn(256).astype(np.float32)),
            (2, 102, "User2", np.random.randn(256).astype(np.float32)),
        ]
        
        service.load_gait_data(embeddings)
        
        assert len(service._gait_cache) == 2
        assert service._gait_matrix is not None
        assert service._gait_matrix.shape == (2, 256)
    
    def test_load_empty_data_sets_none_matrix(self, service):
        """Should set matrix to None when loading empty data."""
        service.load_reid_data([])
        
        assert service._reid_cache == []
        assert service._reid_matrix is None


class TestMatchingServiceAddVector:
    """Tests for adding vectors at runtime."""
    
    @pytest.fixture
    def service(self):
        """Create a MatchingService with mocked engines."""
        mock_reid = Mock()
        mock_reid.embedding_size = 1280
        mock_gait = Mock()
        mock_gait.embedding_size = 256
        
        with patch('src.core.services.matching_service.get_reid_engine', return_value=mock_reid), \
             patch('src.core.services.matching_service.get_gait_engine', return_value=mock_gait):
            from src.core.services.matching_service import MatchingService
            return MatchingService()
    
    def test_add_reid_vector_sets_dirty_flag(self, service):
        """Should mark matrix as dirty instead of immediate rebuild."""
        vector = np.random.randn(1280).astype(np.float32)
        
        service.add_reid_vector(user_id=101, name="NewUser", vector=vector)
        
        assert len(service._reid_cache) == 1
        assert service._reid_matrix_dirty is True
        # Matrix should NOT be built yet (lazy)
        assert service._reid_matrix is None
    
    def test_add_reid_vector_rejects_wrong_dimension(self, service):
        """Should reject vectors with wrong dimensions."""
        wrong_vector = np.random.randn(512).astype(np.float32)  # Wrong size
        
        service.add_reid_vector(user_id=101, name="NewUser", vector=wrong_vector)
        
        assert len(service._reid_cache) == 0  # Not added
    
    def test_add_gait_vector_sets_dirty_flag(self, service):
        """Should mark gait matrix as dirty."""
        vector = np.random.randn(256).astype(np.float32)
        
        service.add_gait_vector(user_id=101, name="NewUser", vector=vector)
        
        assert len(service._gait_cache) == 1
        assert service._gait_matrix_dirty is True


class TestMatchingServiceMatch:
    """Tests for matching functionality."""
    
    @pytest.fixture
    def service_with_data(self):
        """Create a MatchingService with preloaded data."""
        mock_reid = Mock()
        mock_reid.embedding_size = 1280
        mock_reid.compare_embeddings = Mock(return_value=("User1", 101, 0.95))
        
        mock_gait = Mock()
        mock_gait.embedding_size = 256
        mock_gait.compare_embeddings = Mock(return_value=("User1", 101, 0.88))
        
        with patch('src.core.services.matching_service.get_reid_engine', return_value=mock_reid), \
             patch('src.core.services.matching_service.get_gait_engine', return_value=mock_gait):
            from src.core.services.matching_service import MatchingService
            service = MatchingService()
        
        # Preload some data
        embeddings = [
            (1, 101, "User1", np.random.randn(1280).astype(np.float32)),
            (2, 102, "User2", np.random.randn(1280).astype(np.float32)),
        ]
        service.load_reid_data(embeddings)
        
        return service
    
    def test_match_reid_uses_engine(self, service_with_data):
        """Should use reid engine for comparison."""
        query_vector = np.random.randn(1280).astype(np.float32)
        
        result = service_with_data.match_reid(query_vector)
        
        assert result is not None
        service_with_data._reid_engine.compare_embeddings.assert_called_once()
    
    def test_match_reid_empty_cache_returns_none(self):
        """Should return None when cache is empty."""
        with patch('src.core.services.matching_service.get_reid_engine'), \
             patch('src.core.services.matching_service.get_gait_engine'):
            from src.core.services.matching_service import MatchingService
            service = MatchingService()
        
        query_vector = np.random.randn(1280).astype(np.float32)
        result = service.match_reid(query_vector)
        
        assert result is None
    
    def test_match_rebuilds_dirty_matrix(self):
        """Should rebuild matrix on match if dirty flag is set."""
        mock_reid = Mock()
        mock_reid.embedding_size = 1280
        mock_reid.compare_embeddings = Mock(return_value=("User1", 101, 0.95))
        
        with patch('src.core.services.matching_service.get_reid_engine', return_value=mock_reid), \
             patch('src.core.services.matching_service.get_gait_engine'):
            from src.core.services.matching_service import MatchingService
            service = MatchingService()
        
        # Add vector (sets dirty flag)
        vector1 = np.random.randn(1280).astype(np.float32)
        service.add_reid_vector(user_id=101, name="User1", vector=vector1)
        
        assert service._reid_matrix_dirty is True
        assert service._reid_matrix is None
        
        # Perform match (should trigger lazy rebuild)
        query = np.random.randn(1280).astype(np.float32)
        service.match_reid(query)
        
        # Matrix should now be built
        assert service._reid_matrix_dirty is False
        assert service._reid_matrix is not None
        assert service._reid_matrix.shape == (1, 1280)


class TestMatchingServiceIntegration:
    """Integration-ish tests for full flow."""
    
    def test_full_reid_flow(self):
        """Test complete Re-ID flow: load → add → match."""
        mock_reid = Mock()
        mock_reid.embedding_size = 1280
        mock_reid.compare_embeddings = Mock(return_value=("User1", 101, 0.92))
        
        with patch('src.core.services.matching_service.get_reid_engine', return_value=mock_reid), \
             patch('src.core.services.matching_service.get_gait_engine'):
            from src.core.services.matching_service import MatchingService
            service = MatchingService()
        
        # 1. Load initial data
        initial_data = [
            (1, 101, "User1", np.random.randn(1280).astype(np.float32)),
        ]
        service.load_reid_data(initial_data)
        assert service._reid_matrix.shape == (1, 1280)
        
        # 2. Add new vector at runtime
        new_vector = np.random.randn(1280).astype(np.float32)
        service.add_reid_vector(user_id=102, name="User2", vector=new_vector)
        assert service._reid_matrix_dirty is True
        
        # 3. Match (triggers lazy rebuild)
        query = np.random.randn(1280).astype(np.float32)
        result = service.match_reid(query)
        
        # Matrix should be rebuilt with 2 vectors
        assert service._reid_matrix.shape == (2, 1280)
        assert service._reid_matrix_dirty is False
        assert result is not None
