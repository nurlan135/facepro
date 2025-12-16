# Implementation Tasks

## Task 1: CameraPreviewThread yaratmaq

**File:** `src/ui/camera_preview.py`

**Description:** Background-da kamera preview-u üçün QThread sinfi yaratmaq.

**Requirements Addressed:** REQ-3, REQ-4

**Acceptance Criteria:**
- [ ] `CameraPreviewThread` sinfi `QThread`-dən miras alır
- [ ] `frame_ready` signal-ı frame hazır olduqda emit olunur
- [ ] `error` signal-ı xəta baş verdikdə emit olunur
- [ ] `stop()` metodu thread-i təhlükəsiz dayandırır
- [ ] Preview 500ms intervalda yenilənir
- [ ] OpenCV `VideoCapture` düzgün release olunur

**Code Skeleton:**
```python
from PyQt6.QtCore import QThread, pyqtSignal
import cv2

class CameraPreviewThread(QThread):
    frame_ready = pyqtSignal(int, object)  # device_id, frame
    error = pyqtSignal(int, str)  # device_id, error_message
    
    def __init__(self, device_id: int, parent=None):
        super().__init__(parent)
        self._device_id = device_id
        self._running = False
        self._cap = None
    
    def run(self):
        # Implementation
        pass
    
    def stop(self):
        self._running = False
```

---

## Task 2: CameraCard widget yaratmaq

**File:** `src/ui/camera_preview.py`

**Description:** Lokal kamera üçün preview kartı widget-i yaratmaq.

**Requirements Addressed:** REQ-3, REQ-4

**Acceptance Criteria:**
- [ ] `CameraCard` sinfi `QFrame`-dən miras alır
- [ ] 160x120 preview thumbnail göstərir
- [ ] Kamera adı, resolution, FPS göstərir
- [ ] "Bu Kameranı Seç" düyməsi var
- [ ] `selected` signal-ı seçildikdə emit olunur
- [ ] `update_preview(frame)` metodu preview-u yeniləyir
- [ ] `show_error(message)` metodu xəta göstərir
- [ ] Dark theme styling tətbiq olunub

**Code Skeleton:**
```python
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal

class CameraCard(QFrame):
    selected = pyqtSignal(int, dict)  # device_id, camera_info
    
    def __init__(self, device_id: int, info: dict, parent=None):
        super().__init__(parent)
        self._device_id = device_id
        self._info = info
        self._setup_ui()
    
    def _setup_ui(self):
        # Implementation
        pass
    
    def update_preview(self, frame):
        # Implementation
        pass
    
    def show_error(self, message: str):
        # Implementation
        pass
```

---

## Task 3: LocalCameraSelector dialog yaratmaq

**File:** `src/ui/camera_dialogs.py`

**Description:** Lokal kameraları aşkarlayıb önizləmə ilə göstərən dialog.

**Requirements Addressed:** REQ-1, REQ-3, REQ-4, REQ-5

**Acceptance Criteria:**
- [ ] `LocalCameraSelector` sinfi `QDialog`-dan miras alır
- [ ] Dialog açıldıqda avtomatik kamera scan başlayır
- [ ] "Kameralar axtarılır..." loading göstərilir
- [ ] Tapılan hər kamera üçün `CameraCard` yaradılır
- [ ] Kamera tapılmadıqda xəbərdarlıq göstərilir
- [ ] Maksimum 4 eyni vaxtda preview aktiv olur
- [ ] "Geri" düyməsi type selector-a qayıdır
- [ ] Dialog bağlananda bütün preview-lar dayandırılır
- [ ] `get_camera_data()` seçilmiş kamera data-sını qaytarır

**Code Skeleton:**
```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QLabel, QPushButton
from PyQt6.QtCore import Qt

class LocalCameraSelector(QDialog):
    MAX_CONCURRENT_PREVIEWS = 4
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._preview_threads = []
        self._camera_cards = []
        self._selected_camera = None
        self._setup_ui()
        self._scan_cameras()
    
    def _setup_ui(self):
        # Implementation
        pass
    
    def _scan_cameras(self):
        # Implementation
        pass
    
    def _on_camera_selected(self, device_id: int, info: dict):
        # Implementation
        pass
    
    def _stop_previews(self):
        # Implementation
        pass
    
    def closeEvent(self, event):
        self._stop_previews()
        super().closeEvent(event)
    
    def get_camera_data(self) -> dict:
        return self._selected_camera
```

---

## Task 4: RTSPConfigDialog yaratmaq

**File:** `src/ui/camera_dialogs.py`

**Description:** RTSP kamera konfiqurasiyası üçün təkmilləşdirilmiş dialog.

**Requirements Addressed:** REQ-1, REQ-2, REQ-4, REQ-5

**Acceptance Criteria:**
- [ ] `RTSPConfigDialog` sinfi `QDialog`-dan miras alır
- [ ] Ayrı input field-lər: IP, Port, Username, Password, Brand, Channel, Stream
- [ ] URL real-time generasiya olunur və göstərilir
- [ ] Password URL preview-da mask olunur (****)
- [ ] "Test Bağlantı" düyməsi bağlantını yoxlayır
- [ ] Test zamanı loading indicator göstərilir
- [ ] Test uğurlu olduqda bir frame preview göstərilir
- [ ] IP validation (format yoxlanışı)
- [ ] "Geri" düyməsi type selector-a qayıdır
- [ ] "Saxla" düyməsi kamera data-sını saxlayır
- [ ] Boş sahələr üçün validation xətası göstərilir

**Code Skeleton:**
```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                              QSpinBox, QComboBox, QPushButton, QLabel, QGroupBox)
from PyQt6.QtCore import Qt
import re

class RTSPConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera_data = None
        self._setup_ui()
    
    def _setup_ui(self):
        # Implementation
        pass
    
    def _update_url_preview(self):
        # Implementation
        pass
    
    def _validate_ip(self, ip: str) -> bool:
        # Implementation
        pass
    
    def _test_connection(self):
        # Implementation
        pass
    
    def _save(self):
        # Implementation
        pass
    
    def get_camera_data(self) -> dict:
        return self._camera_data
```

---

## Task 5: i18n translations əlavə etmək

**File:** `src/utils/i18n.py`

**Description:** Yeni dialoqular üçün Azərbaycan, İngilis və Rus dillərində tərcümələr əlavə etmək.

**Requirements Addressed:** All (UI text)

**Acceptance Criteria:**
- [ ] Aşağıdakı key-lər üçün AZ, EN, RU tərcümələri əlavə olunub:
  - `rtsp_config_title`
  - `local_camera_title`
  - `scanning_cameras`
  - `no_cameras_found`
  - `test_connection`
  - `connection_success`
  - `connection_failed`
  - `connection_timeout`
  - `auth_failed`
  - `select_this_camera`
  - `ip_address`
  - `port`
  - `username`
  - `password`
  - `brand`
  - `channel`
  - `stream_type`
  - `main_stream`
  - `sub_stream`
  - `url_preview`
  - `back`
  - `invalid_ip`
  - `camera_in_use`
  - `permission_denied`
  - `camera_name`
  - `resolution`
  - `fps`

---

## Task 6: SettingsDialog inteqrasiyası

**File:** `src/ui/settings_dialog.py`

**Description:** Yeni dialoquları SettingsDialog-a inteqrasiya etmək.

**Requirements Addressed:** REQ-1

**Acceptance Criteria:**
- [ ] `_add_camera()` metodu yenilənib
- [ ] RTSP seçildikdə `RTSPConfigDialog` açılır
- [ ] Local seçildikdə `LocalCameraSelector` açılır
- [ ] Mövcud `CameraDialog` RTSP redaktəsi üçün saxlanılır
- [ ] Import-lar əlavə olunub

**Code Changes:**
```python
# settings_dialog.py-ə əlavə
from src.ui.camera_dialogs import RTSPConfigDialog, LocalCameraSelector

def _add_camera(self):
    type_selector = CameraTypeSelector(parent=self)
    if type_selector.exec() != QDialog.DialogCode.Accepted:
        return
    
    if type_selector.selected_type == "rtsp":
        dialog = RTSPConfigDialog(parent=self)
    else:
        dialog = LocalCameraSelector(parent=self)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        camera_data = dialog.get_camera_data()
        if camera_data:
            self._cameras.append(camera_data)
            self._refresh_camera_list()
```

---

## Task 7: Test və debug

**Description:** Bütün funksionallığı test etmək.

**Requirements Addressed:** All

**Acceptance Criteria:**
- [ ] Lokal kamera aşkarlanır və preview göstərilir



- [ ] Lokal kamera seçilib əlavə olunur
- [ ] RTSP konfiqurasiya dialoqu düzgün işləyir
- [ ] URL düzgün generasiya olunur
- [ ] Test connection işləyir (real RTSP ilə)
- [ ] Validation xətaları düzgün göstərilir
- [ ] Dialog bağlananda resurslar azad olunur
- [ ] Dil dəyişdikdə UI yenilənir

---

## Implementation Order

1. **Task 1** - CameraPreviewThread (dependency for Task 2, 3)
2. **Task 2** - CameraCard (dependency for Task 3)
3. **Task 5** - i18n translations (parallel)
4. **Task 3** - LocalCameraSelector
5. **Task 4** - RTSPConfigDialog
6. **Task 6** - SettingsDialog integration
7. **Task 7** - Testing

## Estimated Time

| Task | Estimated Time |
|------|----------------|
| Task 1 | 30 min |
| Task 2 | 45 min |
| Task 3 | 60 min |
| Task 4 | 60 min |
| Task 5 | 20 min |
| Task 6 | 15 min |
| Task 7 | 30 min |
| **Total** | **~4.5 saat** |
