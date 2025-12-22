
import pytest
import numpy as np
import time
from unittest.mock import Mock, patch, MagicMock

from src.core.services.recognition_service import RecognitionService
from src.core.detection import Detection, DetectionType

class TestRecognitionService:
    @pytest.fixture
    def mock_service(self, mock_storage_worker):
        # Mocking heavy dependencies
        with patch('src.core.services.recognition_service.FaceRecognizer') as MockFace, \
             patch('src.core.services.recognition_service.get_reid_engine') as mock_get_reid, \
             patch('src.core.services.recognition_service.get_gait_engine') as mock_get_gait, \
             patch('src.core.services.recognition_service.MatchingService') as MockMatching, \
             patch('src.core.services.recognition_service.EmbeddingRepository') as MockRepo:
            
            # Setup mocks
            mock_face = MockFace.return_value
            mock_reid = mock_get_reid.return_value
            mock_gait = mock_get_gait.return_value
            mock_matching = MockMatching.return_value
            
            # Initialize service
            service = RecognitionService(mock_storage_worker)
            
            # Attach mocks to service for assertion
            service.mock_face = mock_face
            service.mock_reid = mock_reid
            service.mock_gait = mock_gait
            service.mock_matching = mock_matching
            service.mock_repo = MockRepo.return_value
            
            return service

    def test_initialization(self, mock_service):
        assert mock_service is not None

    def test_load_data(self, mock_service):
        # Setup return values
        mock_service.mock_face.load_from_database.return_value = "5 faces"
        mock_service.mock_repo.get_reid_embeddings_with_names.return_value = []
        mock_service.mock_repo.get_gait_embeddings_with_names.return_value = []

        mock_service.load_data()

        mock_service.mock_face.load_from_database.assert_called_once()
        mock_service.mock_matching.load_reid_data.assert_called_once()
        mock_service.mock_matching.load_gait_data.assert_called_once()

    def test_process_identity_face_match(self, mock_service, mock_frame, sample_detection):
        # Setup: Face recognizer returns a match
        # name, user_id, confidence, face_visible, face_bbox
        mock_service.mock_face.recognize.return_value = ("John Doe", 1, 0.95, True, (10, 10, 50, 50))

        mock_service.process_identity(mock_frame, sample_detection)

        assert sample_detection.label == "John Doe"
        assert sample_detection.is_known is True
        assert sample_detection.identification_method == 'face'
        assert sample_detection.confidence == 0.95
        
        # Should attempt passive enrollment
        assert mock_service.mock_reid.extract_embedding.called or mock_service._storage_worker.add_reid_task.called

    def test_process_identity_unknown_face_reid_match(self, mock_service, mock_frame, sample_detection):
        # Setup: Face recognizer returns unknown
        mock_service.mock_face.recognize.return_value = (None, None, 0.0, True, (10, 10, 50, 50))
        
        # Setup: ReID returns a match
        mock_service.mock_reid.extract_embedding.return_value = np.zeros((512,))
        
        mock_match = Mock()
        mock_match.user_name = "Jane Doe"
        mock_match.confidence = 0.85
        mock_service.mock_matching.match_reid.return_value = mock_match

        # Mock crop_person helper
        with patch('src.core.services.recognition_service.crop_person') as mock_crop:
            mock_crop.return_value = np.zeros((100, 50, 3))
            
            mock_service.process_identity(mock_frame, sample_detection)

            assert "Jane Doe" in sample_detection.label
            assert "(Re-ID)" in sample_detection.label
            assert sample_detection.is_known is True
            assert sample_detection.identification_method == 'reid'

    def test_should_sample_reid_logic(self, mock_service):
        user_id = 123
        
        # First call - should sample
        assert mock_service._should_sample_reid(user_id) is True
        
        # Manually set last sample to NOW
        mock_service._user_last_sample[user_id] = time.time()
        
        # Immediate second call - should NOT sample (too soon)
        assert mock_service._should_sample_reid(user_id) is False
        
        # Simulate time passing (mocking time.time logic would be cleaner, but modifying internal state works too)
        # Let's modify the internal state to simulate old sample
        mock_service._user_last_sample[user_id] = time.time() - 3.0 # > 2.0s interval
        
        assert mock_service._should_sample_reid(user_id) is True

    def test_passive_enrollment_limits(self, mock_service, mock_frame, sample_detection):
        user_id = 100
        name = "Test User"
        
        # Mock helper
        with patch('src.core.services.recognition_service.crop_person') as mock_crop:
            mock_crop.return_value = np.zeros((100, 50, 3))
            mock_service.mock_reid.extract_embedding.return_value = np.zeros((512,))
            
            # Hit max samples
            mock_service._user_reid_samples[user_id] = RecognitionService.REID_MAX_SAMPLES
            
            mock_service._passive_enrollment(mock_frame, sample_detection, user_id, name)
            
            # Should NOT add task because limit reached
            mock_service._storage_worker.add_reid_task.assert_not_called()

