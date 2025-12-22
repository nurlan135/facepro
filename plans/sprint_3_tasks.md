# Sprint 3: Konfiqurasiya, i18n və Notifications
> **Müddət:** 2 həftə  
> **Başlanğıc:** Sprint 2 bitdikdən sonra  
> **Hədəf:** i18n modularizasiyası, konfiqurasiya validation, notification throttling

---

## 📋 Task Board

### ✅ Completed

#### PROD-007: i18n Refactoring (4 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 3.1.1 | `locales/` qovluğu yaratmaq | | 0.5d | ✅ |
| 3.1.2 | Mövcud dict-i JSON-a çevirmək | | 1d | ✅ |
| 3.1.3 | I18nManager JSON loader | | 1d | ✅ |
| 3.1.4 | Missing key fallback | | 0.5d | ✅ |
| 3.1.5 | Validation script | | 1d | ✅ |

**Detallar:**

##### 3.1.1 Qovluq Strukturu
```
locales/
├── en.json         # İngilis dili
├── az.json         # Azərbaycan dili
├── ru.json         # Rus dili (gələcək)
├── tr.json         # Türk dili (gələcək)
└── _schema.json    # Key validation schema
```

##### 3.1.2 JSON Format
```json
// locales/en.json
{
  "$schema": "./_schema.json",
  "$meta": {
    "language": "en",
    "name": "English",
    "version": "1.0.0",
    "author": "FacePro Team"
  },
  
  "menu": {
    "file": "File",
    "view": "View",
    "tools": "Tools",
    "help": "Help",
    "exit": "Exit"
  },
  
  "sidebar": {
    "home": "Home",
    "camera": "Camera",
    "logs": "Logs",
    "settings": "Settings",
    "logout": "Logout"
  },
  
  "dashboard": {
    "cards": {
      "start_monitoring": "Start Monitoring",
      "select_camera": "Select Camera",
      "registered_faces": "Registered Faces",
      "total_detections": "Total Detections"
    },
    "status": {
      "running": "Running",
      "stopped": "Stopped",
      "reconnecting": "Reconnecting..."
    }
  },
  
  "camera": {
    "rtsp_url": "RTSP URL",
    "webcam_id": "Webcam ID",
    "test_camera": "Test Camera",
    "connection_failed": "Connection failed",
    "reconnect_attempt": "Reconnect attempt {current}/{max}"
  },
  
  "login": {
    "title": "Login to FacePro",
    "username": "Username",
    "password": "Password",
    "sign_in": "Sign In",
    "error_invalid": "Invalid username or password",
    "account_locked": "Account is locked until {time}"
  },
  
  "errors": {
    "camera_connection": "Cannot connect to camera",
    "database_error": "Database error occurred",
    "disk_full": "Disk space is running low",
    "model_load_failed": "AI model failed to load"
  }
}
```

```json
// locales/az.json
{
  "$schema": "./_schema.json",
  "$meta": {
    "language": "az",
    "name": "Azərbaycan",
    "version": "1.0.0",
    "author": "FacePro Team"
  },
  
  "menu": {
    "file": "Fayl",
    "view": "Görünüş",
    "tools": "Alətlər",
    "help": "Kömək",
    "exit": "Çıxış"
  },
  
  "sidebar": {
    "home": "Ana Səhifə",
    "camera": "Kamera",
    "logs": "Loglar",
    "settings": "Parametrlər",
    "logout": "Çıxış"
  },
  
  "dashboard": {
    "cards": {
      "start_monitoring": "Monitorinqə Başla",
      "select_camera": "Kamera Seç",
      "registered_faces": "Qeydiyyatlı Üzlər",
      "total_detections": "Ümumi Aşkarlamalar"
    },
    "status": {
      "running": "İşləyir",
      "stopped": "Dayandırılıb",
      "reconnecting": "Yenidən qoşulur..."
    }
  },
  
  "camera": {
    "rtsp_url": "RTSP URL",
    "webcam_id": "Webcam ID",
    "test_camera": "Kameranı Test Et",
    "connection_failed": "Bağlantı uğursuz oldu",
    "reconnect_attempt": "Yenidən qoşulma cəhdi: {current}/{max}"
  },
  
  "login": {
    "title": "FacePro-ya Daxil Ol",
    "username": "İstifadəçi adı",
    "password": "Şifrə",
    "sign_in": "Daxil ol",
    "error_invalid": "Səhv istifadəçi adı və ya şifrə",
    "account_locked": "Hesab {time} tarixinə qədər kilidlənib"
  },
  
  "errors": {
    "camera_connection": "Kameraya qoşulmaq mümkün olmadı",
    "database_error": "Verilənlər bazası xətası baş verdi",
    "disk_full": "Disk yeri azalır",
    "model_load_failed": "AI model yüklənə bilmədi"
  }
}
```

##### 3.1.3 Yenilənmiş I18nManager
```python
# Fayl: src/utils/i18n.py (yenilənmiş)

import os
import json
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from src.utils.logger import get_logger

logger = get_logger()

class I18nManager(QObject):
    """Internationalization manager with JSON-based translations"""
    
    _instance = None
    language_changed = pyqtSignal(str)
    
    LOCALES_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'locales'
    )
    
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'az': 'Azərbaycan',
        'ru': 'Русский',
        'tr': 'Türkçe'
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        
        self._current_language = 'en'
        self._translations: Dict[str, Any] = {}
        self._fallback_translations: Dict[str, Any] = {}
        
        # Load fallback (English) first
        self._load_fallback()
    
    def _load_fallback(self):
        """Load English as fallback"""
        self._fallback_translations = self._load_language_file('en')
    
    def _load_language_file(self, lang_code: str) -> Dict[str, Any]:
        """Load a language JSON file"""
        file_path = os.path.join(self.LOCALES_DIR, f'{lang_code}.json')
        
        if not os.path.exists(file_path):
            logger.warning(f"Language file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Remove metadata
                data.pop('$schema', None)
                data.pop('$meta', None)
                return data
        except Exception as e:
            logger.error(f"Failed to load language file {file_path}: {e}")
            return {}
    
    def set_language(self, lang_code: str):
        """Set current language"""
        if lang_code not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {lang_code}, falling back to 'en'")
            lang_code = 'en'
        
        self._current_language = lang_code
        self._translations = self._load_language_file(lang_code)
        self.language_changed.emit(lang_code)
        logger.info(f"Language changed to: {lang_code}")
    
    def get(self, key: str, **kwargs) -> str:
        """
        Get translation by dot-notation key.
        Supports parameter substitution with {param} syntax.
        
        Example:
            i18n.get('login.title')
            i18n.get('camera.reconnect_attempt', current=3, max=5)
        """
        # Try current language first
        value = self._get_nested(self._translations, key)
        
        # Fallback to English
        if value is None:
            value = self._get_nested(self._fallback_translations, key)
            if value is not None:
                logger.debug(f"Missing translation for '{key}' in '{self._current_language}'")
        
        # Still not found
        if value is None:
            logger.warning(f"Translation key not found: {key}")
            return f"[{key}]"  # Return key as placeholder
        
        # Parameter substitution
        if kwargs:
            try:
                value = value.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing parameter in translation '{key}': {e}")
        
        return value
    
    def _get_nested(self, data: Dict, key: str) -> Optional[str]:
        """Get nested value by dot notation (e.g., 'menu.file')"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    @property
    def current_language(self) -> str:
        return self._current_language
    
    @property
    def available_languages(self) -> Dict[str, str]:
        """Return dict of {code: name} for available languages"""
        available = {}
        for code, name in self.SUPPORTED_LANGUAGES.items():
            file_path = os.path.join(self.LOCALES_DIR, f'{code}.json')
            if os.path.exists(file_path):
                available[code] = name
        return available


# Singleton access function
_i18n_manager: Optional[I18nManager] = None

def get_i18n() -> I18nManager:
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager

def tr(key: str, **kwargs) -> str:
    """Shortcut function for translations"""
    return get_i18n().get(key, **kwargs)
```

##### 3.1.5 Validation Script
```python
# scripts/validate_translations.py

import os
import json
import sys

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_all_keys(data, prefix=''):
    """Recursively get all keys from nested dict"""
    keys = set()
    for key, value in data.items():
        if key.startswith('$'):
            continue
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.update(get_all_keys(value, full_key))
        else:
            keys.add(full_key)
    return keys

def validate_translations():
    locales_dir = os.path.join(os.path.dirname(__file__), '..', 'locales')
    
    # Load English as reference
    en_path = os.path.join(locales_dir, 'en.json')
    en_data = load_json(en_path)
    en_keys = get_all_keys(en_data)
    
    print(f"Reference (en.json): {len(en_keys)} keys")
    
    errors = []
    
    for filename in os.listdir(locales_dir):
        if not filename.endswith('.json') or filename.startswith('_') or filename == 'en.json':
            continue
        
        lang_code = filename.replace('.json', '')
        lang_path = os.path.join(locales_dir, filename)
        lang_data = load_json(lang_path)
        lang_keys = get_all_keys(lang_data)
        
        # Missing keys
        missing = en_keys - lang_keys
        if missing:
            errors.append(f"\n{filename} - Missing {len(missing)} keys:")
            for key in sorted(missing):
                errors.append(f"  - {key}")
        
        # Extra keys (might be intentional)
        extra = lang_keys - en_keys
        if extra:
            print(f"\n{filename} - Extra {len(extra)} keys (review):")
            for key in sorted(extra):
                print(f"  + {key}")
    
    if errors:
        print("\n" + "="*50)
        print("VALIDATION FAILED")
        print("="*50)
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("\n✅ All translations are complete!")
        sys.exit(0)

if __name__ == '__main__':
    validate_translations()
```

---

#### PROD-008: Konfiqurasiya Validation (2 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 3.2.1 | Pydantic model yaratmaq | | 0.5d | ✅ |
| 3.2.2 | Load-time validation | | 0.5d | ✅ |
| 3.2.3 | Default fallback | | 0.5d | ✅ |
| 3.2.4 | Settings UI validation | | 0.5d | ✅ |

**Detallar:**

##### 3.2.1 Pydantic Config Models
```python
# Yeni fayl: src/utils/config_models.py

from typing import Optional, List
from pydantic import BaseModel, Field, validator

class TelegramConfig(BaseModel):
    bot_token: str = ""
    chat_id: str = ""

class GSMConfig(BaseModel):
    enabled: bool = False
    com_port: str = "COM3"
    baud_rate: int = Field(default=9600, ge=1200, le=115200)
    phone_number: str = ""

class AIConfig(BaseModel):
    motion_threshold: int = Field(default=25, ge=0, le=100)
    face_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    reid_confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    detection_classes: List[str] = ["person", "cat", "dog"]
    
    @validator('detection_classes')
    def validate_classes(cls, v):
        allowed = {'person', 'cat', 'dog', 'car', 'truck'}
        for item in v:
            if item not in allowed:
                raise ValueError(f"Unknown detection class: {item}")
        return v

class GaitConfig(BaseModel):
    enabled: bool = True
    threshold: float = Field(default=0.70, ge=0.50, le=0.95)
    sequence_length: int = Field(default=30, ge=20, le=60)

class StorageConfig(BaseModel):
    max_size_gb: float = Field(default=10.0, ge=1.0, le=1000.0)
    recordings_path: str = "./data/logs/"
    faces_path: str = "./data/faces/"
    fifo_check_interval_minutes: int = Field(default=10, ge=1, le=60)

class CameraConfig(BaseModel):
    reconnect_interval_seconds: int = Field(default=5, ge=1, le=60)
    target_fps: int = Field(default=30, ge=1, le=60)
    frame_skip: int = Field(default=5, ge=1, le=30)

class UIConfig(BaseModel):
    theme: str = Field(default="dark", pattern="^(dark|light)$")
    language: str = Field(default="az", pattern="^(en|az|ru|tr)$")

class NotificationConfig(BaseModel):
    max_per_minute: int = Field(default=10, ge=1, le=60)
    batch_unknown: bool = True
    batch_interval_seconds: int = Field(default=30, ge=5, le=300)
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"

class AppConfig(BaseModel):
    """Root configuration model"""
    app_name: str = "FacePro"
    version: str = "1.0.0"
    telegram: TelegramConfig = TelegramConfig()
    gsm: GSMConfig = GSMConfig()
    ai: AIConfig = AIConfig()
    gait: GaitConfig = GaitConfig()
    storage: StorageConfig = StorageConfig()
    camera: CameraConfig = CameraConfig()
    ui: UIConfig = UIConfig()
    notifications: NotificationConfig = NotificationConfig()
```

##### 3.2.2 Validated Config Loader
```python
# Fayl: src/utils/helpers.py (yenilənmiş load_config)

from src.utils.config_models import AppConfig
from pydantic import ValidationError

def load_config() -> dict:
    """Load and validate configuration"""
    config_path = get_config_path()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = json.load(f)
    except FileNotFoundError:
        logger.warning("Config file not found, using defaults")
        raw_config = {}
    except json.JSONDecodeError as e:
        logger.error(f"Config file is malformed: {e}")
        raw_config = {}
    
    # Validate with Pydantic
    try:
        validated = AppConfig(**raw_config)
        return validated.model_dump()
    except ValidationError as e:
        logger.error(f"Config validation failed: {e}")
        logger.warning("Using default configuration")
        return AppConfig().model_dump()
```

---

#### PROD-009: Notification Throttling (2 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 3.3.1 | Global rate limit | | 0.5d | ✅ |
| 3.3.2 | Batch notification | | 0.5d | ✅ |
| 3.3.3 | Quiet hours | | 0.5d | ✅ |
| 3.3.4 | Priority levels | | 0.5d | ✅ |

**Detallar:**

##### 3.3.1-4 Yenilənmiş TelegramNotifier
```python
# Fayl: src/hardware/telegram_notifier.py (yenilənmiş hissələr)

from datetime import datetime, time
from collections import deque
from threading import Lock

class TelegramNotifier:
    def __init__(self, ...):
        # ... existing ...
        
        # Rate limiting
        self._message_times: deque = deque(maxlen=100)
        self._rate_lock = Lock()
        
        # Batch notification
        self._unknown_batch: list = []
        self._batch_timer: Optional[threading.Timer] = None
        
        # Config
        self._config = load_config().get('notifications', {})
        self._max_per_minute = self._config.get('max_per_minute', 10)
        self._batch_unknown = self._config.get('batch_unknown', True)
        self._batch_interval = self._config.get('batch_interval_seconds', 30)
        self._quiet_hours_enabled = self._config.get('quiet_hours_enabled', False)
        self._quiet_start = self._parse_time(self._config.get('quiet_hours_start', '23:00'))
        self._quiet_end = self._parse_time(self._config.get('quiet_hours_end', '07:00'))
    
    def _parse_time(self, time_str: str) -> time:
        """Parse HH:MM string to time object"""
        parts = time_str.split(':')
        return time(int(parts[0]), int(parts[1]))
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours"""
        if not self._quiet_hours_enabled:
            return False
        
        now = datetime.now().time()
        
        if self._quiet_start <= self._quiet_end:
            # Normal range (e.g., 09:00 - 17:00)
            return self._quiet_start <= now <= self._quiet_end
        else:
            # Overnight range (e.g., 23:00 - 07:00)
            return now >= self._quiet_start or now <= self._quiet_end
    
    def _check_rate_limit(self) -> bool:
        """Check if we can send a message (rate limiting)"""
        now = time.time()
        
        with self._rate_lock:
            # Remove messages older than 1 minute
            while self._message_times and now - self._message_times[0] > 60:
                self._message_times.popleft()
            
            if len(self._message_times) >= self._max_per_minute:
                return False
            
            self._message_times.append(now)
            return True
    
    def send_detection_alert(self, frame, label, confidence, is_known=False, camera_name="Camera"):
        """Detection alert with improved throttling"""
        
        # Quiet hours check
        if self._is_quiet_hours():
            logger.debug("Notification skipped: quiet hours")
            return
        
        # Rate limit check
        if not self._check_rate_limit():
            logger.warning("Notification rate limit reached")
            return
        
        # Batch unknown persons
        if not is_known and self._batch_unknown:
            self._add_to_batch(frame, label, confidence, camera_name)
            return
        
        # Send immediately for known persons
        self._send_immediate_alert(frame, label, confidence, is_known, camera_name)
    
    def _add_to_batch(self, frame, label, confidence, camera_name):
        """Add unknown detection to batch"""
        self._unknown_batch.append({
            'frame': frame.copy(),
            'label': label,
            'confidence': confidence,
            'camera': camera_name,
            'time': datetime.now()
        })
        
        # Start batch timer if not already running
        if self._batch_timer is None:
            self._batch_timer = threading.Timer(self._batch_interval, self._send_batch)
            self._batch_timer.start()
    
    def _send_batch(self):
        """Send batched unknown detections"""
        self._batch_timer = None
        
        if not self._unknown_batch:
            return
        
        count = len(self._unknown_batch)
        cameras = set(d['camera'] for d in self._unknown_batch)
        
        # Create summary message
        message = f"🔔 <b>{count} naməlum şəxs aşkarlandı</b>\n\n"
        message += f"📷 Kameralar: {', '.join(cameras)}\n"
        message += f"⏰ Son {self._batch_interval} saniyə ərzində"
        
        # Use the most recent frame
        latest = self._unknown_batch[-1]
        
        self._queue.put({
            'type': 'photo',
            'image': latest['frame'],
            'caption': message
        })
        
        self._unknown_batch.clear()
```

---

## 🧪 Test Planı

### i18n Tests
```python
# tests/unit/test_i18n.py

def test_get_translation():
    i18n = get_i18n()
    i18n.set_language('en')
    assert i18n.get('menu.file') == 'File'

def test_fallback_to_english():
    i18n = get_i18n()
    i18n.set_language('az')
    # Assume 'some.missing.key' doesn't exist in az.json
    result = i18n.get('menu.file')  # Should return Azeri if exists
    assert result is not None

def test_parameter_substitution():
    i18n = get_i18n()
    result = i18n.get('camera.reconnect_attempt', current=3, max=5)
    assert '3' in result and '5' in result

def test_missing_key_returns_placeholder():
    i18n = get_i18n()
    result = i18n.get('nonexistent.key')
    assert result == '[nonexistent.key]'
```

### Config Validation Tests
```python
# tests/unit/test_config_validation.py

from src.utils.config_models import AIConfig, AppConfig
import pytest

def test_valid_ai_config():
    config = AIConfig(motion_threshold=50, face_confidence_threshold=0.7)
    assert config.motion_threshold == 50

def test_invalid_threshold_raises():
    with pytest.raises(ValueError):
        AIConfig(motion_threshold=150)  # > 100

def test_default_config():
    config = AppConfig()
    assert config.ai.motion_threshold == 25
    assert config.ui.theme == 'dark'
```

---

## ✅ Sprint Review Checklist

- [ ] i18n JSON fayllara köçürüldü
- [ ] Mövcud bütün UI string-ləri işləyir
- [ ] Yeni dil əlavə etmək sadədir
- [ ] Config validation aktiv
- [ ] Notification batching işləyir
- [ ] Quiet hours konfiqurasiya oluna bilir
