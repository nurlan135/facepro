
"""
Helpers Unit Tests
Tests for utility functions in src/utils/helpers.py.
"""

import pytest
import os
import json
import numpy as np
from unittest.mock import Mock, patch, mock_open

from src.utils.helpers import (
    resize_with_aspect_ratio,
    crop_person,
    get_app_root,
    load_config,
    save_config,
    build_rtsp_url,
    format_seconds,
    get_timestamp,
    ensure_dir
)

class TestImageHelpers:
    
    @pytest.fixture
    def sample_image(self):
        # 100x200 (H, W) image
        return np.zeros((100, 200, 3), dtype=np.uint8)

    def test_resize_with_aspect_ratio_width(self, sample_image):
        # Target width 100 (half). Height should become 50.
        with patch('cv2.resize') as mock_resize:
            # Mock return
            mock_resize.return_value = np.zeros((50, 100, 3), dtype=np.uint8)
            
            result = resize_with_aspect_ratio(sample_image, target_width=100)
            
            args, kwargs = mock_resize.call_args
            assert args[1] == (100, 50) # (w, h) in cv2.resize
            
    def test_resize_with_aspect_ratio_height(self, sample_image):
        # Target height 50 (half). Width should become 100.
        with patch('cv2.resize') as mock_resize:
            resize_with_aspect_ratio(sample_image, target_height=50)
            args, kwargs = mock_resize.call_args
            assert args[1] == (100, 50)

    def test_crop_person(self, sample_image):
        # Image 100x200 (H=100, W=200)
        # BBox: x1=50, y1=20, x2=100, y2=80 (50x60 dims)
        # Padding=10 -> x1=40, y1=10, x2=110, y2=90
        bbox = (50, 20, 100, 80)
        
        crop = crop_person(sample_image, bbox, padding=10)
        
        # Original slicing: image[y1:y2, x1:x2]
        # Heights: 90-10 = 80
        # Widths: 110-40 = 70
        assert crop.shape == (80, 70, 3)

    def test_crop_person_boundary(self, sample_image):
        # Test padding clipping at boundaries
        # BBox at 0,0
        bbox = (0, 0, 50, 50)
        crop = crop_person(sample_image, bbox, padding=10)
        
        # x1=max(0, -10)=0
        # y1=max(0, -10)=0
        # x2=min(200, 60)=60
        # y2=min(100, 60)=60
        assert crop.shape == (60, 60, 3)

class TestConfigHelpers:
    
    def test_get_app_root(self):
        root = get_app_root()
        assert os.path.exists(root)
        # It should be the project root usually (containing src, tests, etc)
        # But depending on how pytest is run, it might be the dir of helpers.py parent parent parent
        # We just verify it returns a string path
        assert isinstance(root, str)

    def test_load_config_defaults(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            config = load_config('nonexistent.json')
            assert config == {}

    def test_load_config_success(self):
        mock_data = json.dumps({"test": 123})
        with patch('builtins.open', mock_open(read_data=mock_data)):
            config = load_config('test.json')
            assert config == {"test": 123}

    def test_save_config_success(self):
        with patch('builtins.open', mock_open()) as m:
            success = save_config({"a": 1}, 'test.json')
            assert success is True
            m.assert_called_once()

    def test_save_config_fail(self):
        with patch('builtins.open', side_effect=IOError):
            success = save_config({"a": 1}, 'test.json')
            assert success is False

class TestStringHelpers:
    
    def test_build_rtsp_url_hikvision(self):
        url = build_rtsp_url("192.168.1.10", "user", "pass", brand="hikvision")
        assert "rtsp://user:pass@192.168.1.10:554/Streaming/Channels/101" in url

    def test_build_rtsp_url_generic(self):
        url = build_rtsp_url("1.2.3.4", "admin", "admin", brand="generic", stream=1)
        assert "rtsp://admin:admin@1.2.3.4:554/stream2" in url

    def test_format_seconds(self):
        assert format_seconds(3661) == "01:01:01"
        assert format_seconds(65) == "00:01:05"
        assert format_seconds(0) == "00:00:00"

    def test_get_timestamp(self):
        ts = get_timestamp()
        # Should be roughly like YYYY-MM-DD HH:MM:SS
        assert "-" in ts and ":" in ts

class TestFileHelpers:
    def test_ensure_dir(self):
        with patch('os.makedirs') as mock_makedirs:
            assert ensure_dir("/tmp/test") is True
            mock_makedirs.assert_called_with("/tmp/test", exist_ok=True)
            
    def test_ensure_dir_fail(self):
        with patch('os.makedirs', side_effect=OSError):
            assert ensure_dir("/tmp/fail") is False
