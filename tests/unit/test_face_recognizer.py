
"""
FaceRecognizer Unit Tests
Tests for face recognition functionality using mocks for heavy backends.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.core.face_recognizer import FaceRecognizer

class TestFaceRecognizer:
    
    @pytest.fixture
    def mock_repo(self):
        with patch('src.core.face_recognizer.EmbeddingRepository') as MockRepo:
            repo_instance = MockRepo.return_value
            yield repo_instance

    @pytest.fixture
    def mock_adapter(self):
        with patch('src.core.detectors.insightface_adapter.InsightFaceAdapter') as MockAdapter:
            adapter_instance = MockAdapter.return_value
            yield adapter_instance

    @pytest.fixture
    def recognizer(self, mock_repo):
        # Prevent actual loading of backends during init if any
        return FaceRecognizer(backend='insightface')

    def test_initialization(self, recognizer):
        assert recognizer is not None
        assert recognizer.backend == 'insightface'
        assert recognizer.embedding_dim == 512
        assert recognizer.known_count == 0

    def test_lazy_load_insightface(self, recognizer, mock_adapter):
        # Should initiate load on first use
        recognizer._load_insightface()
        
        assert recognizer._insightface_adapter is not None
        # Verify it's our mock
        # Note: Since we patched the class, referencing the class in code creates a mock
        pass 

    def test_load_from_database(self, recognizer, mock_repo):
        # Setup mock data: user_id, name, encoding (512 float array)
        mock_encoding = np.random.rand(512).astype(np.float32)
        mock_repo.get_all_face_encodings_with_names.return_value = [
            (1, "User1", mock_encoding),
            (2, "User2", mock_encoding)
        ]

        count = recognizer.load_from_database()

        assert count == 2
        assert recognizer.known_count == 2
        assert "User1" in recognizer._known_encodings
        assert recognizer.get_user_id("User2") == 2
        
        # Test dimension mismatch handling
        mock_repo.get_all_face_encodings_with_names.return_value = [
            (3, "User3", np.zeros((128,))) # Wrong dim for insightface
        ]
        count = recognizer.load_from_database()
        assert count == 0 # Should skip

    def test_recognize_insightface(self, recognizer, mock_adapter):
        # Mock crop_person to return a dummy image
        with patch('src.core.face_recognizer.crop_person') as mock_crop:
            mock_crop.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
            
            # Setup Adapter mocks
            # detect_faces returns list of dicts {bbox, kps, det_score, content_score, similarity, embedding}
            fake_face = {
                'bbox': [10, 10, 50, 50],
                'embedding': np.zeros((512,), dtype=np.float32)
            }
            mock_adapter.detect_faces.return_value = [fake_face]
            
            # find_best_match returns (name, score)
            mock_adapter.find_best_match.return_value = ("KnownUser", 0.85)
            
            # Pre-load some known faces logic (not strictly needed as adapter handles matching abstraction in ref code)
            # Actually, standard logic calls adapter.find_best_match with self._known_encodings
            
            # Manually inject known encodings so the condition `if self._known_encodings:` passes
            recognizer._known_encodings["KnownUser"] = [np.zeros((512,))]
            recognizer._name_to_id["KnownUser"] = 101

            # Call recognize
            frame = np.zeros((640, 480, 3), dtype=np.uint8)
            bbox = (0, 0, 100, 100)
            
            name, user_id, conf, visible, face_bbox = recognizer.recognize(frame, bbox)
            
            assert name == "KnownUser"
            assert user_id == 101
            assert conf == 0.85
            assert visible is True
            # Check bbox projection
            # Original (0,0), local (10,10,50,50) -> global (10,10,50,50)
            assert face_bbox == (10, 10, 50, 50)

    def test_add_known_face(self, recognizer, mock_adapter):
        # Mock embedding extraction
        mock_adapter.get_embedding.return_value = np.zeros((512,), dtype=np.float32)
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        success = recognizer.add_known_face("NewUser", img)
        
        assert success is True
        assert "NewUser" in recognizer._known_encodings
        assert len(recognizer._known_encodings["NewUser"]) == 1

    def test_get_embedding_for_image(self, recognizer, mock_adapter):
        expected_emb = np.ones((512,), dtype=np.float32)
        mock_adapter.get_embedding.return_value = expected_emb
        
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = recognizer.get_embedding_for_image(img)
        
        np.testing.assert_array_equal(result, expected_emb)
