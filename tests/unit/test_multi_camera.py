"""
Sprint 1 Unit Tests: Multi-Camera Support
Tests for YOLO tracking, track ID namespacing, and passive enrollment.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

# Test imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestTrackIdNamespacing:
    """Tests for multi-camera track ID namespacing (PROD-002 Task 1.2.4)"""
    
    def test_get_global_track_id_camera_0(self):
        """Kamera 0 üçün track ID dəyişməməli."""
        from src.core.object_detector import get_global_track_id
        
        assert get_global_track_id(0, 5) == 5
        assert get_global_track_id(0, 100) == 100
        assert get_global_track_id(0, 0) == 0
    
    def test_get_global_track_id_camera_1(self):
        """Kamera 1 üçün track ID 100000 ilə başlamalı."""
        from src.core.object_detector import get_global_track_id
        
        assert get_global_track_id(1, 5) == 100005
        assert get_global_track_id(1, 100) == 100100
        assert get_global_track_id(1, 0) == 100000
    
    def test_get_global_track_id_camera_2(self):
        """Kamera 2 üçün track ID 200000 ilə başlamalı."""
        from src.core.object_detector import get_global_track_id
        
        assert get_global_track_id(2, 5) == 200005
        assert get_global_track_id(2, 999) == 200999
    
    def test_get_global_track_id_invalid(self):
        """Invalid (mənfi) track ID-lər dəyişməməli."""
        from src.core.object_detector import get_global_track_id
        
        assert get_global_track_id(0, -1) == -1
        assert get_global_track_id(1, -1) == -1
        assert get_global_track_id(5, -1) == -1
    
    def test_get_global_track_id_uniqueness(self):
        """Müxtəlif kameralardan eyni lokal track ID konfliktsiz olmalı."""
        from src.core.object_detector import get_global_track_id
        
        # Eyni lokal track ID, müxtəlif kameralar
        local_id = 42
        global_ids = [get_global_track_id(i, local_id) for i in range(5)]
        
        # Hamısı unikal olmalı
        assert len(global_ids) == len(set(global_ids))


class TestPassiveEnrollmentSampling:
    """Tests for time-based passive enrollment (PROD-003 Tasks 1.3.1-1.3.4)"""
    
    def test_should_sample_reid_first_time(self):
        """İlk dəfə sample götürülməli."""
        from src.core.services.recognition_service import RecognitionService
        
        mock_storage = Mock()
        service = RecognitionService(mock_storage)
        
        # İlk dəfə - sample götürülməli
        assert service._should_sample_reid(user_id=1) is True
    
    def test_should_sample_reid_interval(self):
        """İnterval keçmədən sample götürülməməli."""
        from src.core.services.recognition_service import RecognitionService
        
        mock_storage = Mock()
        service = RecognitionService(mock_storage)
        
        # İlk sample
        user_id = 1
        service._user_last_sample[user_id] = time.time()
        service._user_reid_samples[user_id] = 1
        
        # İnterval keçməyib - sample götürülməməli
        assert service._should_sample_reid(user_id) is False
    
    def test_should_sample_reid_after_interval(self):
        """İnterval keçdikdən sonra sample götürülməli."""
        from src.core.services.recognition_service import RecognitionService
        
        mock_storage = Mock()
        service = RecognitionService(mock_storage)
        
        user_id = 1
        # 3 saniyə əvvəl sample götürüldü (interval 2s)
        service._user_last_sample[user_id] = time.time() - 3.0
        service._user_reid_samples[user_id] = 1
        
        # İnterval keçib - sample götürülməli
        assert service._should_sample_reid(user_id) is True
    
    def test_should_sample_reid_max_limit(self):
        """Max limitə çatdıqda sample götürülməməli."""
        from src.core.services.recognition_service import RecognitionService
        
        mock_storage = Mock()
        service = RecognitionService(mock_storage)
        
        user_id = 1
        # Max limitə çatdı
        service._user_reid_samples[user_id] = service.REID_MAX_SAMPLES
        service._user_last_sample[user_id] = time.time() - 100  # Çox vaxt keçib
        
        # Max limitdə - sample götürülməməli
        assert service._should_sample_reid(user_id) is False
    
    def test_reid_constants_defined(self):
        """Re-ID konstantları düzgün təyin olunub."""
        from src.core.services.recognition_service import RecognitionService
        
        assert hasattr(RecognitionService, 'REID_SAMPLE_INTERVAL')
        assert hasattr(RecognitionService, 'REID_MIN_SAMPLES')
        assert hasattr(RecognitionService, 'REID_MAX_SAMPLES')
        
        assert RecognitionService.REID_SAMPLE_INTERVAL > 0
        assert RecognitionService.REID_MIN_SAMPLES > 0
        assert RecognitionService.REID_MAX_SAMPLES > RecognitionService.REID_MIN_SAMPLES


class TestVideoGridLayouts:
    """Tests for VideoGrid layout presets (PROD-001 Task 1.1.6)"""
    
    @pytest.fixture
    def mock_qt_app(self):
        """Mock Qt application for testing."""
        with patch('src.ui.video_widget.QWidget'):
            with patch('src.ui.video_widget.QLabel'):
                with patch('src.ui.video_widget.QGridLayout'):
                    yield
    
    def test_layout_preset_constants(self):
        """Layout preset konstantları mövcuddur."""
        from src.ui.video_widget import VideoGrid
        
        assert VideoGrid.LAYOUT_1X1 == 1
        assert VideoGrid.LAYOUT_2X2 == 2
        assert VideoGrid.LAYOUT_3X3 == 3
        assert VideoGrid.LAYOUT_4X4 == 4


class TestObjectDetectorTracking:
    """Tests for ObjectDetector tracking functionality (PROD-002)"""
    
    def test_detect_method_has_camera_index(self):
        """detect() metodu camera_index parametri qəbul edir."""
        from src.core.object_detector import ObjectDetector
        import inspect
        
        sig = inspect.signature(ObjectDetector.detect)
        params = list(sig.parameters.keys())
        
        assert 'camera_index' in params
    
    def test_detect_camera_index_default(self):
        """camera_index default olaraq 0 olmalı."""
        from src.core.object_detector import ObjectDetector
        import inspect
        
        sig = inspect.signature(ObjectDetector.detect)
        camera_index_param = sig.parameters.get('camera_index')
        
        assert camera_index_param is not None
        assert camera_index_param.default == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
