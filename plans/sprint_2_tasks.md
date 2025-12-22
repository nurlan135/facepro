# Sprint 2: Test Coverage və Error Handling
> **Müddət:** 2 həftə  
> **Başlanğıc:** 2024-12-22  
> **Hədəf:** 60% test coverage, istifadəçi dostu xəta idarəetməsi

---

## 📋 Task Board

### ✅ Completed

#### PROD-004: Unit Test Coverage (5 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 2.1.1 | pytest-cov konfiqurasiyası | | 0.5d | ✅ Tamamlandı |
| 2.1.2 | Core modul testləri | | 2d | ✅ Tamamlandı |
| 2.1.3 | Database repository testləri | | 1d | ✅ Tamamlandı |
| 2.1.4 | Utils testləri | | 1d | ✅ Tamamlandı |
| 2.1.5 | CI/CD pipeline (GitHub Actions) | | 0.5d | ✅ Tamamlandı |

**Detallar:**

##### 2.1.1 pytest-cov Konfiqurasiyası
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = --cov=src --cov-report=html --cov-report=term-missing
filterwarnings = ignore::DeprecationWarning

# Minimum coverage threshold
[coverage:report]
fail_under = 60
```

```toml
# pyproject.toml (alternativ)
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=html"

[tool.coverage.run]
source = ["src"]
omit = ["src/ui/*", "tests/*"]  # UI testləri ayrıdır
```

##### 2.1.2 Core Modul Testləri

**test_face_recognizer.py**
```python
import pytest
import numpy as np
from src.core.face_recognizer import FaceRecognizer

class TestFaceRecognizer:
    @pytest.fixture
    def recognizer(self):
        return FaceRecognizer(backend='insightface')
    
    def test_init_with_insightface_backend(self, recognizer):
        assert recognizer.backend == 'insightface'
        assert recognizer.embedding_dim == 512
    
    def test_get_encodings_returns_list(self, recognizer):
        dummy_image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = recognizer.get_encodings(dummy_image)
        assert isinstance(result, list)
    
    def test_recognize_no_face_returns_none(self, recognizer):
        blank_image = np.zeros((100, 100, 3), dtype=np.uint8)
        name, user_id, conf, face_visible, face_bbox = recognizer.recognize(blank_image, (0, 0, 100, 100))
        assert name is None
        assert face_visible == False
    
    @pytest.mark.parametrize("tolerance", [0.3, 0.4, 0.5])
    def test_tolerance_setting(self, tolerance):
        recognizer = FaceRecognizer(tolerance=tolerance)
        assert recognizer._tolerance == tolerance
```

**test_reid_engine.py**
```python
import pytest
import numpy as np
from src.core.reid_engine import ReIDEngine, get_reid_engine

class TestReIDEngine:
    @pytest.fixture
    def engine(self):
        return get_reid_engine()
    
    def test_singleton_pattern(self):
        engine1 = get_reid_engine()
        engine2 = get_reid_engine()
        assert engine1 is engine2
    
    def test_extract_embedding_shape(self, engine):
        dummy_person = np.random.randint(0, 255, (300, 150, 3), dtype=np.uint8)
        embedding = engine.extract_embedding(dummy_person)
        assert embedding is not None
        assert embedding.shape == (1280,)
    
    def test_cosine_similarity_same_vector(self, engine):
        vec = np.random.rand(1280).astype(np.float32)
        similarity = engine.cosine_similarity(vec, vec)
        assert similarity == pytest.approx(1.0, abs=0.001)
    
    def test_serialize_deserialize_roundtrip(self, engine):
        original = np.random.rand(1280).astype(np.float32)
        serialized = engine.serialize_embedding(original)
        deserialized = engine.deserialize_embedding(serialized)
        assert np.allclose(original, deserialized)
```

**test_detection_service.py**
```python
import pytest
import numpy as np
from src.core.services.detection_service import DetectionService

class TestDetectionService:
    @pytest.fixture
    def service(self):
        return DetectionService()
    
    def test_detect_returns_tuple(self, service):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = service.detect(frame, "TestCamera")
        assert isinstance(result, tuple)
        assert len(result) == 2
        motion_detected, detections = result
        assert isinstance(motion_detected, bool)
        assert isinstance(detections, list)
    
    def test_set_roi(self, service):
        points = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
        service.set_roi("Camera1", points)
        # ROI düzgün set oldumu yoxla
```

##### 2.1.3 Database Repository Testləri

**conftest.py (Fixtures)**
```python
import pytest
import os
import tempfile
from src.core.database.db_manager import DatabaseManager

@pytest.fixture
def temp_db():
    """Test üçün müvəqqəti database yaradır"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # DatabaseManager-ı bu path ilə initialize et
    original_path = os.environ.get('FACEPRO_DB_PATH')
    os.environ['FACEPRO_DB_PATH'] = path
    
    db = DatabaseManager()
    
    yield db
    
    db.close_connection()
    os.unlink(path)
    
    if original_path:
        os.environ['FACEPRO_DB_PATH'] = original_path
```

**test_user_repository.py**
```python
import pytest
from src.core.database.repositories.user_repository import UserRepository

class TestUserRepository:
    @pytest.fixture
    def repo(self, temp_db):
        return UserRepository()
    
    def test_add_user(self, repo):
        user_id = repo.add_user("Test User")
        assert user_id > 0
    
    def test_get_user_by_id(self, repo):
        user_id = repo.add_user("John Doe")
        user = repo.get_user(user_id)
        assert user['name'] == "John Doe"
    
    def test_delete_user(self, repo):
        user_id = repo.add_user("To Delete")
        repo.delete_user(user_id)
        user = repo.get_user(user_id)
        assert user is None
```

##### 2.1.5 CI/CD Pipeline

**.github/workflows/test.yml**
```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
```

---

#### PROD-005: User-Facing Error Handling (3 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 2.2.1 | ErrorNotificationService singleton | | 0.5d | ✅ Tamamlandı |
| 2.2.2 | Toast notification sistemi | | 1d | ✅ Tamamlandı |
| 2.2.3 | Kamera status indicators | | 0.5d | ✅ Tamamlandı |
| 2.2.4 | AI processing error feedback | | 0.5d | 🔲 Növbəti sprint |
| 2.2.5 | Error history in logs | | 0.5d | ✅ History metodları var |

**Detallar:**

##### 2.2.1 ErrorNotificationService
```python
# Yeni fayl: src/utils/error_service.py

from enum import Enum
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
from datetime import datetime

class ErrorLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ErrorEvent:
    level: ErrorLevel
    title: str
    message: str
    timestamp: datetime
    source: str  # "camera", "ai", "database", "storage"
    recoverable: bool = True
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None

class ErrorNotificationService(QObject):
    _instance = None
    
    # Signals
    error_occurred = pyqtSignal(object)  # ErrorEvent
    error_cleared = pyqtSignal(str)       # source
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        self._error_history: list[ErrorEvent] = []
        self._active_errors: dict[str, ErrorEvent] = {}
    
    def report_error(self, 
                     level: ErrorLevel,
                     title: str,
                     message: str,
                     source: str,
                     recoverable: bool = True,
                     action_label: str = None,
                     action_callback: Callable = None):
        """Xəta bildir"""
        event = ErrorEvent(
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            recoverable=recoverable,
            action_label=action_label,
            action_callback=action_callback
        )
        
        self._error_history.append(event)
        self._active_errors[source] = event
        self.error_occurred.emit(event)
    
    def clear_error(self, source: str):
        """Xətanı təmizlə (problem həll olundu)"""
        if source in self._active_errors:
            del self._active_errors[source]
            self.error_cleared.emit(source)
    
    def get_history(self, limit: int = 100) -> list[ErrorEvent]:
        return self._error_history[-limit:]

def get_error_service() -> ErrorNotificationService:
    return ErrorNotificationService()
```

##### 2.2.2 Toast Notification Widget
```python
# Yeni fayl: src/ui/components/toast_widget.py

from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation
from PyQt6.QtGui import QColor

class ToastWidget(QWidget):
    """Pop-up notification widget"""
    
    COLORS = {
        'info': '#3498db',
        'warning': '#f39c12',
        'error': '#e74c3c',
        'critical': '#c0392b'
    }
    
    def __init__(self, event, parent=None):
        super().__init__(parent)
        self._event = event
        self._setup_ui()
        self._start_auto_dismiss()
    
    def _setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QHBoxLayout(self)
        
        # Icon
        icon_map = {'info': 'ℹ️', 'warning': '⚠️', 'error': '❌', 'critical': '🔴'}
        icon = QLabel(icon_map.get(self._event.level.value, 'ℹ️'))
        layout.addWidget(icon)
        
        # Message
        msg = QLabel(f"<b>{self._event.title}</b><br>{self._event.message}")
        msg.setWordWrap(True)
        layout.addWidget(msg, 1)
        
        # Action button (optional)
        if self._event.action_label:
            btn = QPushButton(self._event.action_label)
            btn.clicked.connect(self._on_action)
            layout.addWidget(btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        # Styling
        color = self.COLORS.get(self._event.level.value, '#3498db')
        self.setStyleSheet(f"""
            ToastWidget {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
    
    def _start_auto_dismiss(self):
        duration = 5000 if self._event.level == ErrorLevel.INFO else 10000
        QTimer.singleShot(duration, self.close)
    
    def _on_action(self):
        if self._event.action_callback:
            self._event.action_callback()
        self.close()
```

##### 2.2.3 Kamera Status İnteqrasiyası
```python
# Fayl: src/core/camera_thread.py

# _connect() metoduna əlavə:
from src.utils.error_service import get_error_service, ErrorLevel

def _connect(self):
    # ... existing code ...
    
    if not self._cap.isOpened():
        get_error_service().report_error(
            level=ErrorLevel.ERROR,
            title="Kamera bağlantısı uğursuz",
            message=f"'{self._config.name}' kamerasına qoşulmaq mümkün olmadı.",
            source=f"camera_{self._config.name}",
            recoverable=True,
            action_label="Yenidən cəhd et",
            action_callback=self._manual_reconnect
        )

def _on_connected_successfully(self):
    get_error_service().clear_error(f"camera_{self._config.name}")
```

---

#### PROD-006: Kamera Reconnect UX (2 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 2.3.1 | Reconnect counter UI | | 0.5d | ✅ Tamamlandı |
| 2.3.2 | Reconnect interval settings | | 0.5d | 🔲 Növbəti sprint |
| 2.3.3 | Manual reconnect button | | 0.5d | ✅ request_reconnect signal |
| 2.3.4 | Status icon system | | 0.5d | ✅ CameraStatus enum |

**Detallar:**

##### 2.3.1-4 VideoWidget Status Overlay
```python
# Fayl: src/ui/video_widget.py

class CameraStatus(Enum):
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    OFFLINE = "offline"

class VideoWidget(QLabel):
    def __init__(self, camera_name: str = "Camera", parent=None):
        # ... existing ...
        self._status = CameraStatus.OFFLINE
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        
        # Status overlay
        self._status_overlay = QWidget(self)
        self._setup_status_overlay()
    
    def _setup_status_overlay(self):
        layout = QVBoxLayout(self._status_overlay)
        
        self._status_icon = QLabel("🔴")
        self._status_text = QLabel("Bağlı deyil")
        self._reconnect_info = QLabel("")
        self._manual_reconnect_btn = QPushButton("Yenidən qoşul")
        self._manual_reconnect_btn.hide()
        self._manual_reconnect_btn.clicked.connect(self.request_reconnect)
        
        layout.addWidget(self._status_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_text, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._reconnect_info, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._manual_reconnect_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def set_status(self, status: CameraStatus, attempt: int = 0, max_attempts: int = 5):
        self._status = status
        self._reconnect_attempts = attempt
        
        if status == CameraStatus.CONNECTED:
            self._status_overlay.hide()
        elif status == CameraStatus.RECONNECTING:
            self._status_icon.setText("🟡")
            self._status_text.setText("Yenidən qoşulur...")
            self._reconnect_info.setText(f"Cəhd: {attempt}/{max_attempts}")
            self._manual_reconnect_btn.hide()
            self._status_overlay.show()
        elif status == CameraStatus.FAILED:
            self._status_icon.setText("🔴")
            self._status_text.setText("Qoşulmaq mümkün olmadı")
            self._reconnect_info.setText("Avtomatik cəhdlər tükəndi")
            self._manual_reconnect_btn.show()
            self._status_overlay.show()
    
    request_reconnect = pyqtSignal()  # Signal to camera worker
```

---

## 🧪 Test Coverage Report Template

```
---------- coverage: ... ----------
Name                                      Stmts   Miss  Cover
--------------------------------------------------------------
src/core/face_recognizer.py                 150     45    70%
src/core/reid_engine.py                     180     54    70%
src/core/gait_engine.py                     160     64    60%
src/core/services/detection_service.py       60     18    70%
src/core/services/recognition_service.py    100     40    60%
src/core/database/db_manager.py             120     48    60%
src/utils/auth_manager.py                   200     60    70%
--------------------------------------------------------------
TOTAL                                       970    329    66%
```

---

## ✅ Sprint Review Checklist

- [ ] Test coverage >= 60%
- [ ] Bütün yeni testlər keçir
- [ ] Error notification sistemi işləyir
- [ ] Kamera reconnect UI implementasiya olunub
- [ ] CI/CD pipeline aktiv
- [ ] Documentation yeniləndi
