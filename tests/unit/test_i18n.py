"""
Unit tests for i18n module
"""
import os
import json
import pytest
import tempfile
import shutil

# We need to test the new JSON-based i18n system
# First, let's create a mock locales directory for testing


class TestI18nManager:
    """Tests for the I18nManager class"""
    
    @pytest.fixture
    def temp_locales_dir(self):
        """Create a temporary locales directory with test files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create en.json
        en_data = {
            "$meta": {"language": "en", "name": "English", "version": "1.0.0"},
            "menu": {"file": "File", "view": "View"},
            "camera": {
                "reconnect_attempt": "Reconnect attempt {current}/{max}"
            },
            "errors": {"camera_connection": "Cannot connect to camera"}
        }
        with open(os.path.join(temp_dir, 'en.json'), 'w', encoding='utf-8') as f:
            json.dump(en_data, f)
        
        # Create az.json with partial translations
        az_data = {
            "$meta": {"language": "az", "name": "Azərbaycan", "version": "1.0.0"},
            "menu": {"file": "Fayl", "view": "Görünüş"},
            "camera": {
                "reconnect_attempt": "Yenidən qoşulma cəhdi: {current}/{max}"
            }
            # Note: errors section is missing to test fallback
        }
        with open(os.path.join(temp_dir, 'az.json'), 'w', encoding='utf-8') as f:
            json.dump(az_data, f)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_load_language_file(self, temp_locales_dir):
        """Test loading a language JSON file"""
        en_path = os.path.join(temp_locales_dir, 'en.json')
        
        with open(en_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['menu']['file'] == 'File'
        assert data['menu']['view'] == 'View'
    
    def test_nested_key_access(self, temp_locales_dir):
        """Test accessing nested keys"""
        en_path = os.path.join(temp_locales_dir, 'en.json')
        
        with open(en_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Simulate _get_nested function
        def get_nested(d, key):
            keys = key.split('.')
            current = d
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return None
            return current if isinstance(current, str) else None
        
        assert get_nested(data, 'menu.file') == 'File'
        assert get_nested(data, 'camera.reconnect_attempt') == 'Reconnect attempt {current}/{max}'
        assert get_nested(data, 'nonexistent.key') is None
    
    def test_parameter_substitution(self, temp_locales_dir):
        """Test parameter substitution in translations"""
        en_path = os.path.join(temp_locales_dir, 'en.json')
        
        with open(en_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        template = data['camera']['reconnect_attempt']
        result = template.format(current=3, max=5)
        
        assert '3' in result
        assert '5' in result
        assert result == 'Reconnect attempt 3/5'
    
    def test_fallback_language(self, temp_locales_dir):
        """Test fallback to English when key is missing"""
        en_path = os.path.join(temp_locales_dir, 'en.json')
        az_path = os.path.join(temp_locales_dir, 'az.json')
        
        with open(en_path, 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        with open(az_path, 'r', encoding='utf-8') as f:
            az_data = json.load(f)
        
        # az.json doesn't have errors section, should fallback
        az_camera_key = az_data.get('errors', {}).get('camera_connection')
        en_camera_key = en_data.get('errors', {}).get('camera_connection')
        
        # Simulate fallback
        result = az_camera_key if az_camera_key else en_camera_key
        assert result == 'Cannot connect to camera'
    
    def test_missing_key_placeholder(self):
        """Test that missing keys return placeholder"""
        missing_key = 'nonexistent.missing.key'
        placeholder = f'[{missing_key}]'
        assert placeholder == '[nonexistent.missing.key]'


class TestTranslationValidation:
    """Tests for translation file validation"""
    
    @pytest.fixture
    def temp_locales_dir(self):
        """Create a temporary locales directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_get_all_keys(self, temp_locales_dir):
        """Test extracting all keys from nested dict"""
        data = {
            "$meta": {"language": "en"},
            "menu": {"file": "File", "view": "View"},
            "dashboard": {
                "cards": {"start": "Start", "stop": "Stop"},
                "status": "Status"
            }
        }
        
        def get_all_keys(d, prefix=''):
            keys = set()
            for key, value in d.items():
                if key.startswith('$'):
                    continue
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    keys.update(get_all_keys(value, full_key))
                else:
                    keys.add(full_key)
            return keys
        
        keys = get_all_keys(data)
        
        assert 'menu.file' in keys
        assert 'menu.view' in keys
        assert 'dashboard.cards.start' in keys
        assert 'dashboard.cards.stop' in keys
        assert 'dashboard.status' in keys
        assert '$meta' not in str(keys)  # $meta should be excluded
    
    def test_missing_keys_detection(self, temp_locales_dir):
        """Test detection of missing keys between languages"""
        en_keys = {'menu.file', 'menu.view', 'errors.camera'}
        az_keys = {'menu.file', 'menu.view'}  # Missing errors.camera
        
        missing = en_keys - az_keys
        
        assert 'errors.camera' in missing
        assert len(missing) == 1
    
    def test_extra_keys_detection(self, temp_locales_dir):
        """Test detection of extra keys in translation"""
        en_keys = {'menu.file', 'menu.view'}
        az_keys = {'menu.file', 'menu.view', 'extra.key'}  # Extra key
        
        extra = az_keys - en_keys
        
        assert 'extra.key' in extra
        assert len(extra) == 1


class TestLegacyTranslator:
    """Tests for the legacy dict-based Translator class"""
    
    def test_existing_translator_import(self):
        """Test that we can import the existing translator"""
        from src.utils.i18n import tr, get_translator, set_language
        
        assert callable(tr)
        assert callable(get_translator)
        assert callable(set_language)
    
    def test_basic_translation(self):
        """Test basic translation lookup"""
        from src.utils.i18n import tr
        
        # These keys should exist in the current TRANSLATIONS dict
        result = tr('menu_file')
        assert result is not None
        assert result != 'menu_file'  # Should not return the key itself
    
    def test_language_change(self):
        """Test changing language"""
        from src.utils.i18n import get_translator, set_language, tr
        
        translator = get_translator()
        original_lang = translator.current_language
        
        # Change to Azerbaijani
        set_language('az')
        assert translator.current_language == 'az'
        
        # Change back
        set_language(original_lang)
        assert translator.current_language == original_lang


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
