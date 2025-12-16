# Design Document

## Overview

Bu dizayn sənədi FacePro tətbiqində kamera konfiqurasiya dialoqunun təkmilləşdirilməsini əhatə edir. Mövcud `CameraTypeSelector` və `CameraDialog` sinifləri genişləndiriləcək, lokal kamera aşkarlama və önizləmə funksionallığı əlavə ediləcək.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      SettingsDialog                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    _add_camera()                            ││
│  │                         │                                   ││
│  │                         ▼                                   ││
│  │              ┌──────────────────────┐                       ││
│  │              │  CameraTypeSelector  │                       ││
│  │              │  ┌────────┬────────┐ │                       ││
│  │              │  │ RTSP   │ Local  │ │                       ││
│  │              │  └────┬───┴───┬────┘ │                       ││
│  │              └───────┼───────┼──────┘                       ││
│  │                      │       │                              ││
│  │           ┌──────────┘       └──────────┐                   ││
│  │           ▼                             ▼                   ││
│  │  ┌─────────────────┐         ┌─────────────────────┐        ││
│  │  │ RTSPConfigDialog│         │ LocalCameraSelector │        ││
│  │  │                 │         │                     │        ││
│  │  │ • IP Address    │         │ • Auto-detect       │        ││
│  │  │ • Port          │         │ • Preview cards     │        ││
│  │  │ • Username      │         │ • Resolution info   │        ││
│  │  │ • Password      │         │                     │        ││
│  │  │ • Brand         │         │ ┌─────┐ ┌─────┐     │        ││
│  │  │ • Test button   │         │ │Cam 0│ │Cam 1│     │        ││
│  │  │ • URL preview   │         │ │ 📷  │ │ 📷  │     │        ││
│  │  └─────────────────┘         │ └─────┘ └─────┘     │        ││
│  │                              └─────────────────────┘        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User clicks "Add Camera"
         │
         ▼
CameraTypeSelector.exec()
         │
    ┌────┴────┐
    │         │
    ▼         ▼
  RTSP      Local
    │         │
    ▼         ▼
RTSPConfig  LocalCamera
Dialog      Selector
    │         │
    │    ┌────┴────┐
    │    │ Scan    │
    │    │ cameras │
    │    └────┬────┘
    │         │
    │    ┌────┴────┐
    │    │ Preview │
    │    │ threads │
    │    └────┬────┘
    │         │
    ▼         ▼
camera_data returned
         │
         ▼
Save to cameras.json
```

## Components

### 1. CameraTypeSelector (Mövcud - Dəyişiklik yoxdur)

Artıq implementasiya olunub. İki seçim təqdim edir:
- RTSP/IP Kamera
- Lokal Kamera

### 2. RTSPConfigDialog (Yeni)

RTSP kamera konfiqurasiyası üçün ayrıca dialog.

```python
class RTSPConfigDialog(QDialog):
    """RTSP kamera konfiqurasiya dialoqu."""
    
    def __init__(self, parent=None):
        # UI Elements:
        # - ip_edit: QLineEdit (IP Address)
        # - port_spin: QSpinBox (Port, default 554)
        # - username_edit: QLineEdit
        # - password_edit: QLineEdit (EchoMode.Password)
        # - brand_combo: QComboBox (Hikvision, Dahua, Generic)
        # - channel_spin: QSpinBox (1-16)
        # - stream_combo: QComboBox (Main, Sub)
        # - endpoint_edit: QLineEdit (Custom endpoint)
        # - url_preview: QLabel (Generated URL)
        # - test_btn: QPushButton
        # - preview_label: QLabel (Test frame)
        # - back_btn, save_btn: QPushButton
    
    def _update_url_preview(self):
        """URL-i real-time yeniləyir."""
        pass
    
    def _test_connection(self):
        """RTSP bağlantısını test edir."""
        pass
    
    def get_camera_data(self) -> Dict:
        """Kamera konfiqurasiyasını qaytarır."""
        pass
```

### 3. LocalCameraSelector (Yeni)

Lokal kameraları aşkarlayıb önizləmə ilə göstərən dialog.

```python
class LocalCameraSelector(QDialog):
    """Lokal kamera seçim dialoqu."""
    
    def __init__(self, parent=None):
        # UI Elements:
        # - scroll_area: QScrollArea (kamera kartları üçün)
        # - loading_label: QLabel ("Kameralar axtarılır...")
        # - no_camera_label: QLabel ("Kamera tapılmadı")
        # - back_btn: QPushButton
        
        # Internal:
        # - _preview_threads: List[CameraPreviewThread]
        # - _camera_cards: List[CameraCard]
    
    def _scan_cameras(self):
        """Bütün lokal kameraları aşkarlayır."""
        pass
    
    def _create_camera_card(self, device_id: int, info: Dict) -> QWidget:
        """Kamera kartı yaradır."""
        pass
    
    def _stop_previews(self):
        """Bütün preview thread-ləri dayandırır."""
        pass
    
    def closeEvent(self, event):
        """Dialog bağlananda preview-ları dayandır."""
        self._stop_previews()
        super().closeEvent(event)
```

### 4. CameraPreviewThread (Yeni)

Background-da kamera preview-u üçün thread.

```python
class CameraPreviewThread(QThread):
    """Kamera önizləmə thread-i."""
    
    frame_ready = pyqtSignal(int, object)  # device_id, frame
    error = pyqtSignal(int, str)  # device_id, error_message
    
    def __init__(self, device_id: int, parent=None):
        self._device_id = device_id
        self._running = False
        self._cap = None
    
    def run(self):
        """Preview loop."""
        pass
    
    def stop(self):
        """Thread-i dayandırır."""
        pass
```

### 5. CameraCard (Yeni)

Lokal kamera üçün UI kartı.

```python
class CameraCard(QFrame):
    """Kamera önizləmə kartı."""
    
    selected = pyqtSignal(int, dict)  # device_id, camera_info
    
    def __init__(self, device_id: int, info: Dict, parent=None):
        # UI Elements:
        # - preview_label: QLabel (160x120 thumbnail)
        # - name_label: QLabel ("Camera 0")
        # - resolution_label: QLabel ("1920x1080")
        # - select_btn: QPushButton ("Bu kameranı seç")
    
    def update_preview(self, frame):
        """Preview şəklini yeniləyir."""
        pass
    
    def show_error(self, message: str):
        """Xəta göstərir."""
        pass
```

## Data Models

### Camera Configuration Object

```python
camera_data = {
    "name": str,           # "Webcam" or "IP Camera 1"
    "source": str,         # "0" or "rtsp://..."
    "type": str,           # "Webcam" or "RTSP (IP Camera)"
    "roi_points": List,    # [[x1,y1], [x2,y2], ...]
    
    # RTSP-specific (optional)
    "rtsp_config": {
        "ip": str,
        "port": int,
        "username": str,
        "password": str,    # Encrypted in storage
        "brand": str,
        "channel": int,
        "stream": int       # 0=main, 1=sub
    }
}
```

### Camera Detection Result

```python
camera_info = {
    "device_id": int,      # 0, 1, 2...
    "name": str,           # "Integrated Camera" or "USB Camera"
    "resolution": tuple,   # (1920, 1080)
    "fps": float,          # 30.0
    "backend": str         # "DSHOW" or "V4L2"
}
```

## Correctness Properties

### Property 1: Resource Cleanup
**Invariant:** Bütün kamera preview thread-ləri dialog bağlananda dayandırılmalıdır.

```python
def closeEvent(self, event):
    for thread in self._preview_threads:
        thread.stop()
        thread.wait(1000)  # Max 1 saniyə gözlə
    super().closeEvent(event)
```

### Property 2: Connection Test Timeout
**Invariant:** RTSP bağlantı testi 10 saniyədən çox davam etməməlidir.

```python
def _test_connection(self):
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
    # ...
```

### Property 3: Concurrent Preview Limit
**Invariant:** Eyni anda maksimum 4 kamera preview-u aktiv ola bilər.

```python
MAX_CONCURRENT_PREVIEWS = 4

def _scan_cameras(self):
    # Yalnız ilk 4 kameranı preview et
    for i, cam in enumerate(cameras[:MAX_CONCURRENT_PREVIEWS]):
        self._start_preview(cam)
```

### Property 4: URL Validation
**Invariant:** RTSP URL-i save edilmədən əvvəl format yoxlanmalıdır.

```python
def _validate_rtsp_url(self, url: str) -> bool:
    pattern = r'^rtsp://[\w\-\.:@]+/.*$'
    return bool(re.match(pattern, url))
```

### Property 5: IP Address Validation
**Invariant:** IP adresi düzgün formatda olmalıdır.

```python
def _validate_ip(self, ip: str) -> bool:
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
```

## File Structure

```
src/ui/
├── settings_dialog.py      # Mövcud (dəyişdiriləcək)
├── camera_dialogs.py       # YENİ - RTSPConfigDialog, LocalCameraSelector
└── camera_preview.py       # YENİ - CameraPreviewThread, CameraCard
```

## Integration Points

### 1. SettingsDialog._add_camera() Dəyişikliyi

```python
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
        self._cameras.append(camera_data)
        self._refresh_camera_list()
```

### 2. i18n Keys (Yeni)

```python
# src/utils/i18n.py - translations dict-ə əlavə ediləcək
"rtsp_config_title": "RTSP Kamera Konfiqurasiyası",
"local_camera_title": "Lokal Kamera Seçimi",
"scanning_cameras": "Kameralar axtarılır...",
"no_cameras_found": "Kamera tapılmadı",
"test_connection": "Bağlantını Test Et",
"connection_success": "Bağlantı uğurlu!",
"connection_failed": "Bağlantı uğursuz",
"select_this_camera": "Bu Kameranı Seç",
"ip_address": "IP Ünvanı",
"port": "Port",
"username": "İstifadəçi adı",
"password": "Şifrə",
"brand": "Marka",
"channel": "Kanal",
"stream_type": "Axın növü",
"main_stream": "Əsas axın",
"sub_stream": "Köməkçi axın",
"url_preview": "URL Önizləmə",
"back": "Geri",
"invalid_ip": "Yanlış IP formatı",
"camera_in_use": "Kamera başqa proqram tərəfindən istifadə olunur",
"permission_denied": "Kameraya giriş icazəsi yoxdur"
```

## Error Handling

### RTSP Connection Errors

| Error | Message | Solution |
|-------|---------|----------|
| Timeout | "Bağlantı vaxtı bitdi" | IP/Port yoxlayın |
| Auth Failed | "İstifadəçi adı/şifrə yanlışdır" | Credentials yoxlayın |
| Network Error | "Şəbəkə xətası" | Şəbəkə bağlantısını yoxlayın |
| Invalid URL | "Yanlış URL formatı" | URL-i yoxlayın |

### Local Camera Errors

| Error | Message | Solution |
|-------|---------|----------|
| In Use | "Kamera başqa proqram tərəfindən istifadə olunur" | Digər proqramları bağlayın |
| Permission | "Kameraya giriş icazəsi yoxdur" | Windows Settings-dən icazə verin |
| Not Found | "Kamera tapılmadı" | USB bağlantısını yoxlayın |

## UI Mockups

### RTSPConfigDialog Layout

```
┌─────────────────────────────────────────────┐
│  🌐 RTSP Kamera Konfiqurasiyası             │
├─────────────────────────────────────────────┤
│                                             │
│  IP Ünvanı:    [192.168.1.100        ]     │
│  Port:         [554    ]                    │
│  İstifadəçi:   [admin                ]     │
│  Şifrə:        [••••••             ]       │
│  Marka:        [Hikvision         ▼]       │
│  Kanal:        [1    ]                      │
│  Axın:         [Əsas axın         ▼]       │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ rtsp://admin:****@192.168.1.100:554 │   │
│  │ /Streaming/Channels/101             │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Test Bağlantı]     ┌──────────────┐      │
│                      │   Preview    │      │
│                      │     📷       │      │
│                      └──────────────┘      │
│                                             │
│           [Geri]              [Saxla]       │
└─────────────────────────────────────────────┘
```

### LocalCameraSelector Layout

```
┌─────────────────────────────────────────────┐
│  💻 Lokal Kamera Seçimi                     │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐    ┌─────────────┐        │
│  │   Preview   │    │   Preview   │        │
│  │     📷      │    │     📷      │        │
│  │             │    │             │        │
│  ├─────────────┤    ├─────────────┤        │
│  │ Camera 0    │    │ Camera 1    │        │
│  │ 1920x1080   │    │ 1280x720    │        │
│  │ 30 FPS      │    │ 30 FPS      │        │
│  │             │    │             │        │
│  │ [Seç]       │    │ [Seç]       │        │
│  └─────────────┘    └─────────────┘        │
│                                             │
│                    [Geri]                   │
└─────────────────────────────────────────────┘
```

## Testing Strategy

### Unit Tests
- IP validation function
- URL generation function
- Camera info parsing

### Integration Tests
- Dialog flow (type selection → config → save)
- Camera list refresh after add

### Manual Tests
- RTSP connection with real camera
- Local camera detection
- Preview performance with multiple cameras
