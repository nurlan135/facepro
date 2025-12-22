
"""
Detection Service Unit Tests
Tests for object detection functionality using mocks.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.core.services.detection_service import DetectionService
from src.core.detection import Detection, DetectionType

class TestDetectionService:
    
    @pytest.fixture
    def mock_motion(self):
        with patch('src.core.services.detection_service.MotionDetector') as MockMotion:
            yield MockMotion.return_value

    @pytest.fixture
    def mock_yolo(self):
        with patch('src.core.services.detection_service.ObjectDetector') as MockYolo:
            yield MockYolo.return_value

    @pytest.fixture
    def service(self, mock_motion, mock_yolo):
        return DetectionService()

    def test_initialization(self, service):
        assert service is not None

    def test_detect_no_motion(self, service, mock_motion, mock_yolo):
        # Setup: No motion, no tracking active
        mock_motion.detect.return_value = False
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        has_motion, detections = service.detect(frame, "Cam1")
        
        assert has_motion is False
        assert len(detections) == 0
        mock_yolo.detect.assert_not_called()

    def test_detect_motion_triggers_yolo(self, service, mock_motion, mock_yolo):
        # Setup: Motion detected
        mock_motion.detect.return_value = True
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # YOLO returns one detection
        det = Detection(DetectionType.PERSON, (0,0,10,10), 0.9)
        mock_yolo.detect.return_value = [det]
        
        has_motion, detections = service.detect(frame, "Cam1")
        
        assert has_motion is True
        assert len(detections) == 1
        assert detections[0] == det
        mock_yolo.detect.assert_called_once()

    def test_set_roi(self, service):
        points = [(0,0), (1,1), (0,1)]
        service.set_roi("Cam1", points)
        assert service._camera_rois["Cam1"] == points
        
        service.set_roi("Cam1", [])
        assert "Cam1" not in service._camera_rois

    def test_roi_filtering(self, service, mock_motion, mock_yolo):
        # Setup: Motion detected
        mock_motion.detect.return_value = True
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # YOLO returns two detections: one inside ROI, one outside
        # ROI: Top-Left quarter (0.0, 0.0) to (0.5, 0.5)
        roi_points = [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]
        service.set_roi("Cam1", roi_points)
        
        # Det 1: Center (0.25, 0.25) -> Inside
        det1 = Detection(DetectionType.PERSON, (20, 20, 30, 30), 0.9) # Center ~25,25 on 100x100 -> 0.25, 0.25
        
        # Det 2: Center (0.75, 0.75) -> Outside
        det2 = Detection(DetectionType.PERSON, (70, 70, 80, 80), 0.9) # Center ~75,75 -> 0.75, 0.75
        
        mock_yolo.detect.return_value = [det1, det2]
        
        has_motion, detections = service.detect(frame, "Cam1")
        
        assert len(detections) == 1
        assert detections[0] == det1

class TestObjectDetectorHelper:
    def test_global_track_id(self):
        from src.core.object_detector import get_global_track_id
        
        assert get_global_track_id(0, 5) == 5
        assert get_global_track_id(1, 5) == 100005
        assert get_global_track_id(2, -1) == -1
