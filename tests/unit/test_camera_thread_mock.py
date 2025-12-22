
"""
Unit tests for CameraWorker using mocks.
"""
import pytest
import numpy as np
import time
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtCore import QThread

from src.core.camera_thread import CameraWorker, CameraConfig

class TestCameraWorker:
    
    @pytest.fixture
    def mock_cv2(self):
        with patch('src.core.camera_thread.cv2') as mock:
            yield mock

    @pytest.fixture
    def worker(self, mock_cv2):
        config = CameraConfig(source="0", name="TestCam")
        worker = CameraWorker(config)
        # Prevent actual thread run logic from being blocking/infinite in tests
        # We will test chunks of logic individually
        return worker

    def test_initialization(self, worker):
        assert worker.config.name == "TestCam"
        assert worker.is_connected is False

    def test_connect_success(self, worker, mock_cv2):
        # Setup mock capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            mock_cv2.CAP_PROP_FRAME_WIDTH: 640,
            mock_cv2.CAP_PROP_FRAME_HEIGHT: 480,
            mock_cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        # Mock read for warmup frames
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        
        mock_cv2.VideoCapture.return_value = mock_cap
        
        # Connect signals
        status_spy = Mock()
        worker.connection_status.connect(status_spy)
        
        worker._connect()
        
        assert worker.is_connected is True
        status_spy.assert_called_with(True, "TestCam")
        mock_cv2.VideoCapture.assert_called()

    def test_connect_fail(self, worker, mock_cv2):
        # Setup mock capture to fail
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap
        
        status_spy = Mock()
        error_spy = Mock()
        worker.connection_status.connect(status_spy)
        worker.error_occurred.connect(error_spy)
        
        # Override sleep to speed up test
        with patch('time.sleep'):
             worker._connect()
        
        assert worker.is_connected is False
        error_spy.assert_called()

    def test_is_valid_frame(self, worker):
        # Valid frame
        valid = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        assert worker._is_valid_frame(valid) is True
        
        # Empty
        assert worker._is_valid_frame(None) is False
        assert worker._is_valid_frame(np.array([])) is False
        
        # Too small
        small = np.zeros((50, 50, 3), dtype=np.uint8)
        assert worker._is_valid_frame(small) is False
        
        # Single color/Black
        black = np.zeros((200, 200, 3), dtype=np.uint8)
        assert worker._is_valid_frame(black) is False

    def test_handle_read_failure(self, worker):
        worker.config.reconnect_interval = 0.01
        
        # Mock disconnect
        worker._disconnect = Mock()
        
        # Simulate faults
        worker._max_failures = 5
        for i in range(4):
            worker._handle_read_failure()
            assert worker._consecutive_failures == i + 1
            worker._disconnect.assert_not_called()
            
        # 5th failure triggers reconnect logic
        with patch('time.sleep'):
            worker._handle_read_failure()
            
        assert worker._consecutive_failures == 0
        worker._disconnect.assert_called_once()
