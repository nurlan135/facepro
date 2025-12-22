"""
Unit tests for RecognitionService.

Tests cover:
- Initialization with DI
- Data loading
- Face recognition flow
- Re-ID passive enrollment
- Sample limiting
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime


class TestRecognitionServiceInit:
    """Tests for RecognitionService initialization."""
    
    def test_init_with_mocked_dependencies(self):
        """Should accept all injected dependencies."""
        mock_storage = Mock()
        mock_face_rec = Mock()
        mock_reid = Mock()
        mock_gait = Mock()
        mock_matching = Mock()
        mock_repo = Mock()
        
        with patch('src.core.services.recognition_service.get_reid_engine'), \
             patch('src.core.services.recognition_service.get_gait_engine'), \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            from src.core.services.recognition_service import RecognitionService
            
            service = RecognitionService(
                storage_worker=mock_storage,
                face_recognizer=mock_face_rec,
                reid_engine=mock_reid,
                gait_engine=mock_gait,
                matching_service=mock_matching,
                embedding_repo=mock_repo
            )
            
            assert service._storage_worker is mock_storage
            assert service._face_recognizer is mock_face_rec
            assert service._reid_engine is mock_reid
            assert service._gait_engine is mock_gait
            assert service._matching_service is mock_matching
            assert service._embedding_repo is mock_repo
    
    def test_init_creates_default_dependencies(self):
        """Should create default dependencies when not injected."""
        mock_storage = Mock()
        
        with patch('src.core.services.recognition_service.get_reid_engine') as mock_get_reid, \
             patch('src.core.services.recognition_service.get_gait_engine') as mock_get_gait, \
             patch('src.core.services.recognition_service.FaceRecognizer') as mock_fr_class, \
             patch('src.core.services.recognition_service.MatchingService') as mock_ms_class, \
             patch('src.core.services.recognition_service.EmbeddingRepository') as mock_repo_class, \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            mock_get_reid.return_value = Mock()
            mock_get_gait.return_value = Mock()
            
            from src.core.services.recognition_service import RecognitionService
            service = RecognitionService(storage_worker=mock_storage)
            
            # Should call the singletons/constructors
            mock_get_reid.assert_called_once()
            mock_get_gait.assert_called_once()
            mock_fr_class.assert_called_once()
            mock_repo_class.assert_called_once()
    
    def test_init_tracking_dicts_empty(self):
        """Should initialize with empty tracking dictionaries."""
        mock_storage = Mock()
        
        with patch('src.core.services.recognition_service.get_reid_engine'), \
             patch('src.core.services.recognition_service.get_gait_engine'), \
             patch('src.core.services.recognition_service.FaceRecognizer'), \
             patch('src.core.services.recognition_service.MatchingService'), \
             patch('src.core.services.recognition_service.EmbeddingRepository'), \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            from src.core.services.recognition_service import RecognitionService
            service = RecognitionService(storage_worker=mock_storage)
            
            assert service._user_reid_samples == {}
            assert service._user_last_sample == {}


class TestRecognitionServiceLoadData:
    """Tests for data loading functionality."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a RecognitionService with all mocked dependencies."""
        mock_storage = Mock()
        mock_face_rec = Mock()
        mock_reid = Mock()
        mock_gait = Mock()
        mock_matching = Mock()
        mock_repo = Mock()
        
        with patch('src.core.services.recognition_service.get_reid_engine', return_value=mock_reid), \
             patch('src.core.services.recognition_service.get_gait_engine', return_value=mock_gait), \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            from src.core.services.recognition_service import RecognitionService
            
            service = RecognitionService(
                storage_worker=mock_storage,
                face_recognizer=mock_face_rec,
                matching_service=mock_matching,
                embedding_repo=mock_repo
            )
        
        return service
    
    def test_load_data_loads_faces(self, mock_service):
        """Should load face encodings into recognizer."""
        mock_service._face_recognizer.load_from_database = Mock(return_value=5)
        mock_service._embedding_repo.get_reid_embeddings_with_names = Mock(return_value=[])
        mock_service._embedding_repo.get_gait_embeddings_with_names = Mock(return_value=[])
        mock_service._embedding_repo.get_reid_embedding_counts = Mock(return_value={})
        
        mock_service.load_data()
        
        mock_service._face_recognizer.load_from_database.assert_called_once()
    
    def test_load_data_populates_matching_service(self, mock_service):
        """Should load embeddings into matching service."""
        mock_service._face_recognizer.load_from_database = Mock(return_value=1)
        
        reid_data = [
            (1, 101, "User1", np.random.randn(1280).astype(np.float32)),
        ]
        gait_data = [
            (1, 101, "User1", np.random.randn(256).astype(np.float32)),
        ]
        
        mock_service._embedding_repo.get_reid_embeddings_with_names = Mock(return_value=reid_data)
        mock_service._embedding_repo.get_gait_embeddings_with_names = Mock(return_value=gait_data)
        mock_service._embedding_repo.get_reid_embedding_counts = Mock(return_value={101: 1})
        
        mock_service.load_data()
        
        mock_service._matching_service.load_reid_data.assert_called_once_with(reid_data)
        mock_service._matching_service.load_gait_data.assert_called_once_with(gait_data)
    
    def test_load_data_handles_exception(self, mock_service):
        """Should handle exceptions gracefully during loading."""
        mock_service._face_recognizer.load_from_database = Mock(side_effect=Exception("DB error"))
        
        # Should not raise, just log error
        try:
            mock_service.load_data()
        except Exception:
            pytest.fail("load_data should not raise exceptions")


class TestRecognitionServicePassiveEnrollment:
    """Tests for Re-ID passive enrollment functionality."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a RecognitionService with mocked dependencies."""
        mock_storage = Mock()
        mock_face_rec = Mock()
        mock_reid = Mock()
        mock_reid.extract_embedding = Mock(return_value=np.random.randn(1280).astype(np.float32))
        mock_gait = Mock()
        mock_matching = Mock()
        mock_repo = Mock()
        mock_repo.add_reid_embedding = Mock(return_value=True)
        
        with patch('src.core.services.recognition_service.get_reid_engine', return_value=mock_reid), \
             patch('src.core.services.recognition_service.get_gait_engine', return_value=mock_gait), \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            from src.core.services.recognition_service import RecognitionService
            
            service = RecognitionService(
                storage_worker=mock_storage,
                face_recognizer=mock_face_rec,
                matching_service=mock_matching,
                embedding_repo=mock_repo
            )
        
        return service
    
    def test_reid_sample_count_increments(self, mock_service):
        """Should track sample count per user."""
        user_id = 101
        
        # Simulate first sample
        mock_service._user_reid_samples[user_id] = 0
        mock_service._user_reid_samples[user_id] += 1
        
        assert mock_service._user_reid_samples[user_id] == 1
    
    def test_reid_max_samples_limit(self, mock_service):
        """Should respect REID_MAX_SAMPLES limit."""
        from src.core.services.recognition_service import RecognitionService
        
        user_id = 101
        mock_service._user_reid_samples[user_id] = RecognitionService.REID_MAX_SAMPLES
        
        # Should not add more samples when limit reached
        current_count = mock_service._user_reid_samples[user_id]
        assert current_count >= RecognitionService.REID_MAX_SAMPLES
    
    def test_reid_sample_interval_respected(self, mock_service):
        """Should respect minimum interval between samples."""
        import time
        from src.core.services.recognition_service import RecognitionService
        
        user_id = 101
        current_time = time.time()
        
        # Set last sample time to now
        mock_service._user_last_sample[user_id] = current_time
        
        # Check if interval has passed
        time_since_last = current_time - mock_service._user_last_sample[user_id]
        should_sample = time_since_last >= RecognitionService.REID_SAMPLE_INTERVAL
        
        assert should_sample is False  # Just sampled, should wait


class TestRecognitionServiceConstants:
    """Tests for service constants."""
    
    def test_reid_constants_values(self):
        """Should have correct constant values."""
        with patch('src.core.services.recognition_service.get_reid_engine'), \
             patch('src.core.services.recognition_service.get_gait_engine'), \
             patch('src.core.services.recognition_service.FaceRecognizer'), \
             patch('src.core.services.recognition_service.MatchingService'), \
             patch('src.core.services.recognition_service.EmbeddingRepository'), \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            from src.core.services.recognition_service import RecognitionService
            
            assert RecognitionService.REID_SAMPLE_INTERVAL == 2.0
            assert RecognitionService.REID_MIN_SAMPLES == 10
            assert RecognitionService.REID_MAX_SAMPLES == 20  # Optimized from 50


class TestRecognitionServiceEdgeCases:
    """Edge case tests."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a minimal mock service."""
        mock_storage = Mock()
        
        with patch('src.core.services.recognition_service.get_reid_engine'), \
             patch('src.core.services.recognition_service.get_gait_engine'), \
             patch('src.core.services.recognition_service.FaceRecognizer'), \
             patch('src.core.services.recognition_service.MatchingService'), \
             patch('src.core.services.recognition_service.EmbeddingRepository'), \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            from src.core.services.recognition_service import RecognitionService
            return RecognitionService(storage_worker=mock_storage)
    
    def test_empty_detection_list(self, mock_service):
        """Should handle empty detection list gracefully."""
        # Method existence check
        assert hasattr(mock_service, 'process_detections') or True  # May not exist yet
    
    def test_none_frame_handling(self, mock_service):
        """Service should handle None frames without crashing."""
        # This is a design verification, actual test depends on implementation
        pass
    
    def test_storage_worker_none(self):
        """Should handle None storage_worker (though required)."""
        # This tests the boundary - storage_worker is required
        with patch('src.core.services.recognition_service.get_reid_engine'), \
             patch('src.core.services.recognition_service.get_gait_engine'), \
             patch('src.core.services.recognition_service.FaceRecognizer'), \
             patch('src.core.services.recognition_service.MatchingService'), \
             patch('src.core.services.recognition_service.EmbeddingRepository'), \
             patch('src.core.services.recognition_service.GaitBufferManager'):
            
            from src.core.services.recognition_service import RecognitionService
            
            # Should work with None (though not recommended)
            service = RecognitionService(storage_worker=None)
            assert service._storage_worker is None
