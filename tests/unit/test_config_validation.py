"""
Unit tests for configuration validation models
"""
import pytest
from pydantic import ValidationError


class TestTelegramConfig:
    """Tests for TelegramConfig model"""
    
    def test_default_values(self):
        """Test default values"""
        from src.utils.config_models import TelegramConfig
        
        config = TelegramConfig()
        assert config.bot_token == ""
        assert config.chat_id == ""
    
    def test_custom_values(self):
        """Test custom values"""
        from src.utils.config_models import TelegramConfig
        
        config = TelegramConfig(bot_token="123:ABC", chat_id="456")
        assert config.bot_token == "123:ABC"
        assert config.chat_id == "456"


class TestAIConfig:
    """Tests for AIConfig model"""
    
    def test_default_values(self):
        """Test default values"""
        from src.utils.config_models import AIConfig
        
        config = AIConfig()
        assert config.motion_threshold == 25
        assert config.face_confidence_threshold == 0.6
        assert config.reid_confidence_threshold == 0.75
        assert config.detection_classes == ["person", "cat", "dog"]
    
    def test_valid_threshold(self):
        """Test valid threshold values"""
        from src.utils.config_models import AIConfig
        
        config = AIConfig(motion_threshold=50, face_confidence_threshold=0.8)
        assert config.motion_threshold == 50
        assert config.face_confidence_threshold == 0.8
    
    def test_invalid_motion_threshold_too_high(self):
        """Test that motion_threshold > 100 raises error"""
        from src.utils.config_models import AIConfig
        
        with pytest.raises(ValidationError):
            AIConfig(motion_threshold=150)
    
    def test_invalid_motion_threshold_too_low(self):
        """Test that motion_threshold < 0 raises error"""
        from src.utils.config_models import AIConfig
        
        with pytest.raises(ValidationError):
            AIConfig(motion_threshold=-10)
    
    def test_invalid_confidence_threshold(self):
        """Test that face_confidence_threshold > 1.0 raises error"""
        from src.utils.config_models import AIConfig
        
        with pytest.raises(ValidationError):
            AIConfig(face_confidence_threshold=1.5)
    
    def test_valid_detection_classes(self):
        """Test valid detection classes"""
        from src.utils.config_models import AIConfig
        
        config = AIConfig(detection_classes=["person", "car"])
        assert "person" in config.detection_classes
        assert "car" in config.detection_classes
    
    def test_invalid_detection_class(self):
        """Test that unknown detection class raises error"""
        from src.utils.config_models import AIConfig
        
        with pytest.raises(ValidationError):
            AIConfig(detection_classes=["person", "unknown_class"])


class TestGaitConfig:
    """Tests for GaitConfig model"""
    
    def test_default_values(self):
        """Test default values"""
        from src.utils.config_models import GaitConfig
        
        config = GaitConfig()
        assert config.enabled is True
        assert config.threshold == 0.70
        assert config.sequence_length == 30
    
    def test_threshold_boundaries(self):
        """Test threshold at boundaries"""
        from src.utils.config_models import GaitConfig
        
        # At minimum
        config_min = GaitConfig(threshold=0.50)
        assert config_min.threshold == 0.50
        
        # At maximum
        config_max = GaitConfig(threshold=0.95)
        assert config_max.threshold == 0.95
    
    def test_invalid_threshold(self):
        """Test invalid threshold values"""
        from src.utils.config_models import GaitConfig
        
        with pytest.raises(ValidationError):
            GaitConfig(threshold=0.40)  # Below minimum
        
        with pytest.raises(ValidationError):
            GaitConfig(threshold=0.99)  # Above maximum
    
    def test_sequence_length_boundaries(self):
        """Test sequence_length at boundaries"""
        from src.utils.config_models import GaitConfig
        
        config_min = GaitConfig(sequence_length=20)
        assert config_min.sequence_length == 20
        
        config_max = GaitConfig(sequence_length=60)
        assert config_max.sequence_length == 60


class TestUIConfig:
    """Tests for UIConfig model"""
    
    def test_default_values(self):
        """Test default values"""
        from src.utils.config_models import UIConfig
        
        config = UIConfig()
        assert config.theme == "dark"
        assert config.language == "az"
    
    def test_valid_theme(self):
        """Test valid theme values"""
        from src.utils.config_models import UIConfig
        
        dark = UIConfig(theme="dark")
        assert dark.theme == "dark"
        
        light = UIConfig(theme="light")
        assert light.theme == "light"
    
    def test_invalid_theme(self):
        """Test invalid theme value"""
        from src.utils.config_models import UIConfig
        
        with pytest.raises(ValidationError):
            UIConfig(theme="blue")
    
    def test_valid_language(self):
        """Test valid language values"""
        from src.utils.config_models import UIConfig
        
        for lang in ["en", "az", "ru", "tr"]:
            config = UIConfig(language=lang)
            assert config.language == lang
    
    def test_invalid_language(self):
        """Test invalid language value"""
        from src.utils.config_models import UIConfig
        
        with pytest.raises(ValidationError):
            UIConfig(language="fr")


class TestNotificationConfig:
    """Tests for NotificationConfig model"""
    
    def test_default_values(self):
        """Test default values"""
        from src.utils.config_models import NotificationConfig
        
        config = NotificationConfig()
        assert config.max_per_minute == 10
        assert config.batch_unknown is True
        assert config.batch_interval_seconds == 30
        assert config.quiet_hours_enabled is False
        assert config.quiet_hours_start == "23:00"
        assert config.quiet_hours_end == "07:00"
    
    def test_time_format_validation(self):
        """Test time format validation"""
        from src.utils.config_models import NotificationConfig
        
        # Valid time
        config = NotificationConfig(quiet_hours_start="22:30")
        assert config.quiet_hours_start == "22:30"
    
    def test_invalid_time_format(self):
        """Test invalid time format raises error"""
        from src.utils.config_models import NotificationConfig
        
        with pytest.raises(ValidationError):
            NotificationConfig(quiet_hours_start="25:00")
        
        with pytest.raises(ValidationError):
            NotificationConfig(quiet_hours_end="12:65")


class TestAppConfig:
    """Tests for root AppConfig model"""
    
    def test_default_values(self):
        """Test default root config"""
        from src.utils.config_models import AppConfig
        
        config = AppConfig()
        assert config.app_name == "FacePro"
        assert config.version == "1.0.0"
        assert config.ai.motion_threshold == 25
        assert config.ui.theme == "dark"
        assert config.notifications.batch_unknown is True
    
    def test_nested_config_override(self):
        """Test overriding nested config values"""
        from src.utils.config_models import AppConfig, AIConfig
        
        config = AppConfig(ai=AIConfig(motion_threshold=50))
        assert config.ai.motion_threshold == 50
        # Other defaults should remain
        assert config.ui.theme == "dark"
    
    def test_model_dump(self):
        """Test converting config to dict"""
        from src.utils.config_models import AppConfig
        
        config = AppConfig()
        data = config.model_dump()
        
        assert isinstance(data, dict)
        assert data['app_name'] == "FacePro"
        assert isinstance(data['ai'], dict)
        assert data['ai']['motion_threshold'] == 25
    
    def test_from_dict(self):
        """Test creating config from dict"""
        from src.utils.config_models import AppConfig
        
        data = {
            "app_name": "CustomApp",
            "ai": {"motion_threshold": 75}
        }
        
        config = AppConfig(**data)
        assert config.app_name == "CustomApp"
        assert config.ai.motion_threshold == 75
        # Unspecified values should use defaults
        assert config.version == "1.0.0"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
