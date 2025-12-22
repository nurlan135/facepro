"""
FaceRecognizer Unit Tests
Tests for face recognition functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestFaceRecognizerInit:
    """Test FaceRecognizer initialization."""
    
    def test_import_face_recognizer(self):
        """FaceRecognizer modulu import olunmalı."""
        from src.core.face_recognizer import FaceRecognizer
        assert FaceRecognizer is not None
    
    def test_create_instance(self):
        """FaceRecognizer instansı yaradılmalı."""
        from src.core.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer()
        assert recognizer is not None
    
    def test_default_tolerance(self):
        """Default tolerance dəyəri düzgün olmalı."""
        from src.core.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer()
        assert hasattr(recognizer, '_tolerance')
        # Tolerance 0 ilə 1 arasında olmalı
        assert 0 < recognizer._tolerance <= 1
    
    @pytest.mark.parametrize("tolerance", [0.3, 0.4, 0.5, 0.6])
    def test_custom_tolerance(self, tolerance):
        """Custom tolerance qəbul olunmalı."""
        from src.core.face_recognizer import FaceRecognizer
        recognizer = FaceRecognizer(tolerance=tolerance)
        assert recognizer._tolerance == tolerance


class TestFaceRecognizerMethods:
    """Test FaceRecognizer methods."""
    
    @pytest.fixture
    def recognizer(self):
        from src.core.face_recognizer import FaceRecognizer
        return FaceRecognizer()
    
    def test_get_encodings_exists(self, recognizer):
        """get_encodings metodu mövcud olmalı."""
        assert hasattr(recognizer, 'get_encodings')
        assert callable(recognizer.get_encodings)
    
    def test_recognize_exists(self, recognizer):
        """recognize metodu mövcud olmalı."""
        assert hasattr(recognizer, 'recognize')
        assert callable(recognizer.recognize)
    
    def test_add_known_face_exists(self, recognizer):
        """add_known_face metodu mövcud olmalı."""
        assert hasattr(recognizer, 'add_known_face')
        assert callable(recognizer.add_known_face)
    
    @pytest.mark.skipif(True, reason="Requires InsightFace model to be loaded")
    def test_recognize_returns_tuple(self, recognizer):
        """recognize() metodu tuple qaytarmalı."""
        mock_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = recognizer.recognize(mock_frame, (0, 0, 100, 100))
        assert isinstance(result, tuple)
        assert len(result) == 5  # name, user_id, confidence, face_visible, face_bbox
    
    @pytest.mark.skipif(True, reason="Requires InsightFace model to be loaded")
    def test_recognize_no_face_in_blank_image(self, recognizer):
        """Boş şəkildə üz tapılmamalı."""
        blank_image = np.zeros((100, 100, 3), dtype=np.uint8)
        name, user_id, conf, face_visible, face_bbox = recognizer.recognize(
            blank_image, (0, 0, 100, 100)
        )
        assert name is None
    
    @pytest.mark.skipif(True, reason="Requires InsightFace model to be loaded")
    def test_get_encodings_returns_list(self, recognizer):
        """get_encodings() metodu list qaytarmalı."""
        mock_face_image = np.zeros((160, 160, 3), dtype=np.uint8)
        result = recognizer.get_encodings(mock_face_image)
        assert isinstance(result, list)


class TestFaceRecognizerDatabase:
    """Test database integration."""
    
    @pytest.fixture
    def recognizer(self):
        from src.core.face_recognizer import FaceRecognizer
        return FaceRecognizer()
    
    def test_load_from_database_exists(self, recognizer):
        """load_from_database metodu mövcud olmalı."""
        assert hasattr(recognizer, 'load_from_database')
        assert callable(recognizer.load_from_database)
    
    def test_load_from_database_returns_int(self, recognizer):
        """load_from_database() int qaytarmalı."""
        result = recognizer.load_from_database()
        assert isinstance(result, int)
        assert result >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
