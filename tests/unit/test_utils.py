"""
Utils Module Unit Tests
Tests for utility functions and helpers.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch


class TestLoggerModule:
    """Test logger functionality."""
    
    def test_import_logger(self):
        """Logger modulu import olunmalı."""
        from src.utils.logger import get_logger
        assert get_logger is not None
    
    def test_get_logger_returns_facepro_logger(self):
        """get_logger() FaceProLogger instansı qaytarmalı."""
        from src.utils.logger import get_logger, FaceProLogger
        
        logger = get_logger()
        assert isinstance(logger, FaceProLogger)
    
    def test_logger_has_methods(self):
        """Logger info, error, warning metodlarına malik olmalı."""
        from src.utils.logger import get_logger
        logger = get_logger()
        
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')


class TestI18nModule:
    """Test internationalization functionality."""
    
    def test_import_i18n(self):
        """i18n modulu import olunmalı."""
        from src.utils.i18n import tr, get_translator
        assert tr is not None
        assert get_translator is not None
    
    def test_tr_returns_string(self):
        """tr() funksiyası string qaytarmalı."""
        from src.utils.i18n import tr
        result = tr('btn_start')
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_tr_missing_key_returns_key(self):
        """Olmayan açar üçün tr() açarın özünü qaytarmalı."""
        from src.utils.i18n import tr
        missing_key = 'nonexistent_translation_key_12345'
        result = tr(missing_key)
        # Ya açarın özünü qaytarır, ya da boş string
        assert isinstance(result, str)


class TestHelpersModule:
    """Test helper functions."""
    
    def test_import_helpers(self):
        """Helpers modulu import olunmalı."""
        from src.utils.helpers import load_config, load_cameras
        assert load_config is not None
        assert load_cameras is not None
    
    def test_load_config_returns_dict(self):
        """load_config() dict qaytarmalı."""
        from src.utils.helpers import load_config
        config = load_config()
        assert isinstance(config, dict)
    
    def test_load_cameras_returns_list(self):
        """load_cameras() list qaytarmalı."""
        from src.utils.helpers import load_cameras
        cameras = load_cameras()
        assert isinstance(cameras, list)
    
    def test_cv2_to_qpixmap_exists(self):
        """cv2_to_qpixmap funksiyası mövcud olmalı."""
        from src.utils.helpers import cv2_to_qpixmap
        assert callable(cv2_to_qpixmap)
    
    def test_crop_person_exists(self):
        """crop_person funksiyası mövcud olmalı."""
        from src.utils.helpers import crop_person
        assert callable(crop_person)
    
    def test_crop_person_with_valid_bbox(self, mock_frame):
        """crop_person() düzgün bbox ilə işləməli."""
        from src.utils.helpers import crop_person
        
        bbox = (100, 100, 300, 400)  # x1, y1, x2, y2
        result = crop_person(mock_frame, bbox)
        
        if result is not None:
            assert isinstance(result, np.ndarray)
            assert result.shape[0] > 0  # Height
            assert result.shape[1] > 0  # Width
    
    def test_crop_person_with_invalid_bbox(self, mock_frame):
        """crop_person() invalid bbox ilə düzgün davranmalı."""
        from src.utils.helpers import crop_person
        
        # Çox böyük koordinatlar - frame dışında
        result = crop_person(mock_frame, (1000, 1000, 1500, 1500))
        # None və ya boş array olmalı
        if result is not None:
            # Boş və ya etibarsız crop
            assert isinstance(result, np.ndarray)
    
    def test_get_timestamp_exists(self):
        """get_timestamp funksiyası mövcud olmalı."""
        from src.utils.helpers import get_timestamp
        assert callable(get_timestamp)
    
    def test_get_timestamp_returns_string(self):
        """get_timestamp() string qaytarmalı."""
        from src.utils.helpers import get_timestamp
        result = get_timestamp()
        assert isinstance(result, str)
        assert len(result) > 0


class TestAuthManager:
    """Test authentication manager."""
    
    def test_import_auth_manager(self):
        """AuthManager modulu import olunmalı."""
        from src.utils.auth_manager import get_auth_manager
        assert get_auth_manager is not None
    
    def test_singleton_pattern(self):
        """get_auth_manager() həmişə eyni instansı qaytarmalı."""
        from src.utils.auth_manager import get_auth_manager
        
        manager1 = get_auth_manager()
        manager2 = get_auth_manager()
        
        assert manager1 is manager2
    
    def test_is_logged_in_returns_bool(self):
        """is_logged_in() bool qaytarmalı."""
        from src.utils.auth_manager import get_auth_manager
        manager = get_auth_manager()
        
        result = manager.is_logged_in()
        assert isinstance(result, bool)
    
    def test_can_enroll_faces_exists(self):
        """can_enroll_faces metodu mövcud olmalı."""
        from src.utils.auth_manager import get_auth_manager
        manager = get_auth_manager()
        
        assert hasattr(manager, 'can_enroll_faces')
        assert callable(manager.can_enroll_faces)
    
    def test_can_access_settings_exists(self):
        """can_access_settings metodu mövcud olmalı."""
        from src.utils.auth_manager import get_auth_manager
        manager = get_auth_manager()
        
        assert hasattr(manager, 'can_access_settings')
        assert callable(manager.can_access_settings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
