"""
Detection Service Unit Tests
Tests for object detection functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestDetectionServiceInit:
    """Test DetectionService initialization."""
    
    def test_import_detection_service(self):
        """DetectionService modulu import olunmalı."""
        from src.core.services.detection_service import DetectionService
        assert DetectionService is not None
    
    def test_create_instance(self):
        """DetectionService instansı yaradılmalı."""
        from src.core.services.detection_service import DetectionService
        service = DetectionService()
        assert service is not None


class TestDetectionServiceMethods:
    """Test DetectionService methods."""
    
    @pytest.fixture
    def service(self):
        from src.core.services.detection_service import DetectionService
        return DetectionService()
    
    def test_detect_exists(self, service):
        """detect metodu mövcud olmalı."""
        assert hasattr(service, 'detect')
        assert callable(service.detect)
    
    def test_detect_returns_tuple(self, service, mock_frame):
        """detect() metodu tuple qaytarmalı."""
        result = service.detect(mock_frame, "TestCamera")
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_detect_returns_bool_and_list(self, service, mock_frame):
        """detect() (bool, list) formatında qaytarmalı."""
        motion_detected, detections = service.detect(mock_frame, "TestCamera")
        assert isinstance(motion_detected, bool)
        assert isinstance(detections, list)
    
    def test_set_roi_exists(self, service):
        """set_roi metodu mövcud olmalı."""
        assert hasattr(service, 'set_roi')
        assert callable(service.set_roi)
    
    def test_set_roi_accepts_points(self, service):
        """set_roi() nöqtələri qəbul etməli."""
        points = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
        # Should not raise
        service.set_roi("Camera1", points)


class TestDetectionServiceROI:
    """Test ROI (Region of Interest) functionality."""
    
    @pytest.fixture
    def service(self):
        from src.core.services.detection_service import DetectionService
        return DetectionService()
    
    def test_set_and_clear_roi(self, service):
        """ROI set və clear olunmalı."""
        camera_name = "TestCam"
        points = [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]
        
        service.set_roi(camera_name, points)
        service.set_roi(camera_name, [])  # Clear


class TestObjectDetector:
    """Test ObjectDetector directly."""
    
    def test_import_object_detector(self):
        """ObjectDetector modulu import olunmalı."""
        from src.core.object_detector import ObjectDetector
        assert ObjectDetector is not None
    
    def test_get_global_track_id_function(self):
        """get_global_track_id funksiyası mövcud olmalı."""
        from src.core.object_detector import get_global_track_id
        assert callable(get_global_track_id)
    
    def test_allowed_classes_defined(self):
        """ALLOWED_CLASSES təyin olunmalı."""
        from src.core.object_detector import ObjectDetector
        assert hasattr(ObjectDetector, 'ALLOWED_CLASSES')
        assert ObjectDetector.PERSON_ID in ObjectDetector.ALLOWED_CLASSES
    
    def test_class_ids_correct(self):
        """COCO class ID-ləri düzgün olmalı."""
        from src.core.object_detector import ObjectDetector
        assert ObjectDetector.PERSON_ID == 0
        assert ObjectDetector.CAT_ID == 15
        assert ObjectDetector.DOG_ID == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
