# FacePro - Project Handover Documentation

> **Version:** 1.0.0  
> **Last Updated:** December 17, 2025  
> **Organization:** NurMurDev

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Module Deep Dive](#3-module-deep-dive)
4. [Third-Party Integrations](#4-third-party-integrations)
5. [Security & Vulnerability Audit](#5-security--vulnerability-audit)
6. [Developer Onboarding](#6-developer-onboarding)
7. [Deployment Pipeline & Infrastructure](#7-deployment-pipeline--infrastructure)
8. [Next Steps & Priority Actions](#8-next-steps--priority-actions)

---

## 1. Executive Summary

### 1.1 What is FacePro?

FacePro is a **desktop-based smart security system** built with Python and PyQt6 that provides intelligent surveillance capabilities using local AI processing. The application can:

- **Face Recognition**: Identify known individuals in real-time using the `face_recognition` library (dlib-based)
- **Person Re-Identification (Re-ID)**: Recognize people by their body/clothing when faces aren't visible
- **Gait Recognition**: Identify individuals by their walking patterns
- **Object Detection**: Detect persons, cats, and dogs using YOLOv8
- **Multi-Camera Support**: Connect to webcams, RTSP streams, and DVR systems
- **Real-Time Notifications**: Telegram bot integration for alerts
- **Offline Fallback**: GSM modem SMS alerts when internet is unavailable
- **FIFO Storage Management**: Automatic cleanup of old recordings

### 1.2 Target Users

- Security operators monitoring premises
- Small businesses requiring automated surveillance
- Residential security applications
- Organizations needing person identification without cloud dependencies

### 1.3 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Local AI Processing** | Privacy-first approach, no cloud dependency |
| **PyQt6 GUI** | Cross-platform, native look and feel |
| **SQLite Database** | Simple, serverless, portable |
| **Hardware-Based Licensing** | Offline license validation tied to machine |
| **Multi-Modal Identification** | Face → Re-ID → Gait fallback chain |

---

## 2. System Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FACEPRO APPLICATION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Main Thread │    │ Camera Thread │    │  AI Thread   │                   │
│  │    (UI)      │◄──►│ (CameraWorker)│───►│  (AIWorker)  │                   │
│  │              │    │              │    │              │                   │
│  │  ┌────────┐  │    │ ┌──────────┐ │    │ ┌──────────┐ │                   │
│  │  │PyQt6   │  │    │ │OpenCV    │ │    │ │YOLO      │ │                   │
│  │  │Widgets │  │    │ │Capture   │ │    │ │Detection │ │                   │
│  │  └────────┘  │    │ └──────────┘ │    │ └──────────┘ │                   │
│  │              │    │              │    │ ┌──────────┐ │                   │
│  │  ┌────────┐  │    │ ┌──────────┐ │    │ │Face Rec  │ │                   │
│  │  │Dashboard│  │    │ │Reconnect │ │    │ │(dlib)   │ │                   │
│  │  │Widgets │  │    │ │Logic     │ │    │ └──────────┘ │                   │
│  │  └────────┘  │    │ └──────────┘ │    │ ┌──────────┐ │                   │
│  └──────────────┘    └──────────────┘    │ │Re-ID     │ │                   │
│                                          │ │Engine    │ │                   │
│                                          │ └──────────┘ │                   │
│                                          │ ┌──────────┐ │                   │
│                                          │ │Gait      │ │                   │
│                                          │ │Engine    │ │                   │
│                                          │ └──────────┘ │                   │
│                                          └──────────────┘                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         HARDWARE LAYER                               │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │    │
│  │  │ Telegram Bot    │  │ GSM Modem (SMS) │  │ Storage Cleaner │      │    │
│  │  │ (Async Queue)   │  │ (AT Commands)   │  │ (FIFO Policy)   │      │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         DATA LAYER (SQLite)                          │    │
│  │  • users (registered people)    • face_encodings    • events         │    │
│  │  • app_users (login accounts)   • reid_embeddings   • gait_embeddings│    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Threading Model

FacePro uses Qt's threading model to prevent GUI freezing:

| Thread | Class | Responsibility |
|--------|-------|----------------|
| **Main Thread** | `MainWindow` | PyQt6 event loop, UI rendering, user interactions |
| **Camera Thread(s)** | `CameraWorker` | Video capture, frame delivery, auto-reconnect |
| **AI Thread** | `AIWorker` | Motion detection, object detection, face/Re-ID/gait recognition |
| **Telegram Worker** | Background thread in `TelegramNotifier` | Async notification delivery |
| **Storage Cleaner** | Timer thread in `StorageCleaner` | Periodic FIFO cleanup |

### 2.3 Data Flow

```
Camera → CameraWorker.frame_ready signal → MainWindow → AIWorker.process_frame()
                                                              ↓
                                              AIWorker.frame_processed signal
                                                              ↓
                                              MainWindow._on_frame_processed()
                                                              ↓
                                              CameraPage (display) + LogsPage (events)
                                                              ↓
                                              TelegramNotifier (if unknown person)
```

---

## 3. Module Deep Dive

### 3.1 Core Modules (`src/core/`)

#### 3.1.1 `ai_thread.py` - AI Processing Pipeline

**Purpose:** Central AI processing orchestrator running in a separate QThread.

**Key Class:** `AIWorker(QThread)`

**Processing Pipeline:**
1. **Motion Detection** → Gate to skip frames with no motion (CPU saver)
2. **Object Detection** → YOLO-based person/animal detection
3. **Face Recognition** → dlib-based face encoding matching
4. **Re-ID Engine** → Body/clothing embedding matching (fallback)
5. **Gait Engine** → Walking pattern recognition (final fallback)

**Signals Emitted:**
- `frame_processed(FrameResult)` - Processed frame with detections
- `detection_alert(Detection, frame)` - New person detection event

**Critical Methods:**
```python
_process_frame()      # Main processing pipeline
_process_person()     # Per-person identification logic
_passive_reid_enrollment()   # Auto-enroll body embeddings
_passive_gait_enrollment()   # Auto-enroll gait patterns
```

#### 3.1.2 `camera_thread.py` - Video Capture

**Purpose:** Handles video capture from webcams and RTSP streams.

**Key Classes:**
- `CameraConfig` - Configuration dataclass
- `CameraWorker(QThread)` - Video capture thread
- `CameraManager` - Multi-camera orchestrator

**Features:**
- Auto-reconnect after connection failures
- FPS limiting for CPU efficiency
- Timeout handling for RTSP streams

#### 3.1.3 `face_recognizer.py` - Face Recognition

**Purpose:** Face detection and encoding comparison.

**Dependencies:** `face_recognition` library (requires `dlib`)

**Key Methods:**
```python
add_known_face(name, face_image)  # Manual enrollment
recognize(frame, person_bbox)      # Returns (name, user_id, confidence, face_visible, face_bbox)
load_from_database()               # Load stored encodings
```

#### 3.1.4 `object_detector.py` - YOLO Detection

**Purpose:** YOLOv8-based object detection.

**Allowed Classes:** Person (0), Cat (15), Dog (16)

**Features:**
- Lazy model loading
- Built-in tracking for track_id persistence
- Configurable confidence threshold

#### 3.1.5 `reid_engine.py` - Person Re-Identification

**Purpose:** Body/clothing-based person identification when face isn't visible.

**Model:** EfficientNet-B0 (pretrained, adapted)

**Key Methods:**
```python
extract_embedding(person_image)   # Returns 1280-dim vector
compare_embeddings(query, stored) # Cosine similarity matching
```

#### 3.1.6 `gait_engine.py` - Gait Recognition

**Purpose:** Walking pattern identification using silhouette sequences.

**Model:** ResNet18 adapted for single-channel input

**Process:**
1. Extract silhouette from person bounding box
2. Collect 30 frames of silhouettes
3. Average embeddings for final 256-dim vector
4. Compare with stored patterns

#### 3.1.7 `cleaner.py` - Storage Manager

**Purpose:** FIFO storage management to prevent disk overflow.

**Features:**
- Background timer-based cleanup (every 10 minutes)
- Age-based file deletion (oldest first)
- Configurable max size (default: 10GB)

### 3.2 Utils Modules (`src/utils/`)

#### 3.2.1 `auth_manager.py` - Authentication System

**Purpose:** User authentication and session management.

**Features:**
- SHA-256 password hashing with random salt
- Account lockout (3 failed attempts → 5 min lockout)
- Session timeout (configurable, default 30 min)
- Role-based access control (admin/operator)

**Signals:**
- `logout_requested` - For camera cleanup on logout
- `session_timeout` - For auto-logout handling

#### 3.2.2 `license_manager.py` - Hardware Licensing

**Purpose:** Offline license validation tied to machine hardware.

**Algorithm:**
```
Machine ID = SHA-256(System UUID + Volume Serial + CPU ID)[:16]
License Key = Base32(SHA-256(Machine ID + SECRET_SALT))[:20]
```

**⚠️ SECURITY CONCERN:** Secret salt is hardcoded in source code.

#### 3.2.3 `helpers.py` - Utility Functions

**Purpose:** Common utilities used across the application.

**Key Functions:**
- `cv2_to_qpixmap()` - OpenCV to Qt conversion
- `load_config() / save_config()` - JSON config I/O
- `get_db_path()` - Database path with auto-initialization
- `save_event()` - Event logging to database
- `build_rtsp_url()` - RTSP URL builder for major camera brands

#### 3.2.4 `i18n.py` - Internationalization

**Purpose:** Multi-language support.

**Supported Languages:**
- English (`en`)
- Azerbaijani (`az`)

**Pattern:** Dictionary-based translations with `tr(key)` function.

### 3.3 UI Modules (`src/ui/`)

#### 3.3.1 `main_window.py` - Main Dashboard

**Purpose:** Primary application window with dashboard layout.

**Structure:**
- Sidebar navigation
- Stacked pages (Home, Camera, Logs)
- System tray integration
- Menu bar with role-based items

#### 3.3.2 UI Components (`src/ui/dashboard/`)

| Component | Purpose |
|-----------|---------|
| `SidebarWidget` | Left navigation panel |
| `HomePage` | Statistics and quick actions |
| `CameraPage` | Live video feed display |
| `LogsPage` | Event history with filters |
| `ActivityItem` | Individual log entry widget |

#### 3.3.3 Settings (`src/ui/settings/`)

Modular settings dialog with tabs:
- General (language, theme)
- Camera configuration
- AI thresholds
- Notifications (Telegram, GSM)
- Gait recognition settings

### 3.4 Hardware Modules (`src/hardware/`)

#### 3.4.1 `telegram_notifier.py` - Telegram Integration

**Purpose:** Send real-time alerts via Telegram bot.

**Features:**
- Async queue for message delivery
- Rate limiting (30s per person, 10s global)
- Photo + caption alerts
- Auto-retry mechanism

#### 3.4.2 `gsm_modem.py` - SMS Fallback

**Purpose:** Send SMS alerts when internet is unavailable.

**Protocol:** AT Commands via serial port

**Commands Used:**
```
AT           - Connection test
AT+CMGF=1    - Set text mode
AT+CMGS      - Send SMS
AT+CSQ       - Check signal strength
```

---

## 4. Third-Party Integrations

### 4.1 Telegram Bot API

| Aspect | Details |
|--------|---------|
| **Purpose** | Real-time security alerts with photos |
| **Implementation** | `src/hardware/telegram_notifier.py` |
| **API Methods Used** | `sendMessage`, `sendPhoto`, `getMe` |
| **Rate Limiting** | 30s per person, 10s global minimum |
| **Required Config** | `telegram.bot_token`, `telegram.chat_id` in `settings.json` |
| **Env Variables** | None (stored in config file) |

**Setup Requirements:**
1. Create bot via [@BotFather](https://t.me/botfather)
2. Get bot token
3. Start conversation with bot and get chat ID
4. Configure in Settings → Notifications

**Vendor Lock/Migration Risk:** **LOW**
- Standard HTTP API, easily replaceable with other messaging services
- No proprietary features used

### 4.2 YOLOv8 (Ultralytics)

| Aspect | Details |
|--------|---------|
| **Purpose** | Object detection (person, cat, dog) |
| **Implementation** | `src/core/object_detector.py` |
| **Model Used** | `yolov8n.pt` (nano, fastest) |
| **License** | AGPL-3.0 (commercial license available) |
| **Required Files** | `models/yolov8n.pt` (auto-downloads if missing) |

**Migration Risk:** **MEDIUM**
- Could switch to other YOLO versions or ONNX models
- Ultralytics has specific license terms for commercial use

### 4.3 face_recognition (dlib)

| Aspect | Details |
|--------|---------|
| **Purpose** | Face detection and encoding |
| **Implementation** | `src/core/face_recognizer.py` |
| **License** | MIT (dlib is Boost License) |
| **Installation** | Requires Visual Studio Build Tools on Windows |
| **Required Models** | `face_recognition_models` package |

**Migration Risk:** **MEDIUM-HIGH**
- Deep dependency on dlib's face encoding format
- Stored encodings would need migration if switching libraries
- Consider testing with DeepFace as an alternative

### 4.4 PyTorch/TorchVision

| Aspect | Details |
|--------|---------|
| **Purpose** | Re-ID and Gait recognition models |
| **Implementation** | `src/core/reid_engine.py`, `src/core/gait_engine.py` |
| **Models Used** | EfficientNet-B0, ResNet18 |
| **GPU Support** | CUDA auto-detection, CPU fallback |

**Migration Risk:** **LOW**
- Standard pretrained models
- Easy to swap with ONNX or other frameworks

### 4.5 pyserial

| Aspect | Details |
|--------|---------|
| **Purpose** | GSM modem communication |
| **Implementation** | `src/hardware/gsm_modem.py` |
| **Protocol** | AT Commands over serial port |

**Migration Risk:** **LOW**
- Standard serial communication
- Hardware-dependent (requires USB modem)

### 4.6 Complete Dependency Map

```python
# requirements.txt
PyQt6>=6.4.0              # UI Framework
opencv-python>=4.8.0      # Video processing
Pillow>=9.5.0             # Image handling
ultralytics>=8.0.0        # YOLOv8
torch>=2.0.0              # Deep learning
torchvision>=0.15.0       # Pretrained models
deepface>=0.0.79          # Alternative face rec (unused)
tf-keras>=2.16.0          # DeepFace dependency
numpy>=1.24.0,<2.0.0      # Array operations
pyserial>=3.5             # GSM modem
requests>=2.31.0          # HTTP client
schedule>=1.2.0           # Task scheduling
psutil>=5.9.0             # System monitoring
pytest>=9.0.0             # Testing
hypothesis>=6.100.0       # Property-based testing
```

---

## 5. Security & Vulnerability Audit

### 5.1 CRITICAL Issues (Fix Immediately)

#### 🔴 CRITICAL-01: Hardcoded Telegram API Credentials

**Location:** `config/settings.json` (lines 4-7)
```json
"telegram": {
    "bot_token": "8275886963:AAGrmckSFx20U2Qtiamp-OJf9tZ7ygHYo1M",
    "chat_id": "486493885"
}
```

**Risk:** These credentials are now in version control and should be considered compromised.

**Fix:**
1. **Immediately revoke** this bot token via [@BotFather](https://t.me/botfather)
2. Create a new bot and update credentials
3. Add `config/settings.json` to `.gitignore` or use a template file
4. Consider environment variables for sensitive config:
```python
bot_token = os.environ.get('FACEPRO_TELEGRAM_TOKEN', config.get('bot_token', ''))
```

#### 🔴 CRITICAL-02: Hardcoded License Salt

**Location:** `src/utils/license_manager.py` (line 21)
```python
_SECRET_SALT = "FaceGuard_v1_$uper$ecure_2025!"
```

**Also duplicated:** `admin_keygen.py` (line 21)

**Risk:** Anyone with source code access can generate valid license keys for any machine.

**Fix Options:**
1. **Obfuscation**: Use PyArmor or similar to protect the salt
2. **Server-based validation**: Move license validation to a server
3. **Hardware dongle**: Use a physical dongle for license validation
4. **At minimum**: Store salt as environment variable and remove from source

### 5.2 HIGH Severity Issues

#### 🟠 HIGH-01: SHA-256 without Iterations for Password Hashing

**Location:** `src/utils/auth_manager.py` (lines 105-123)

**Current Implementation:**
```python
salted_password = password.encode('utf-8') + salt
password_hash = hashlib.sha256(salted_password).hexdigest()
```

**Risk:** Single SHA-256 is too fast, vulnerable to brute-force attacks.

**Fix:** Use `bcrypt`, `scrypt`, or `argon2`:
```python
import bcrypt

def hash_password(self, password: str) -> Tuple[str, str]:
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8'), salt.decode('utf-8')
```

#### 🟠 HIGH-02: SQL Injection Vulnerability

**Location:** `src/utils/auth_manager.py` (line 288-289)

**Vulnerable Code:**
```python
cursor.execute(f'''
    UPDATE app_users SET {", ".join(updates)} WHERE id = ?
''', params)
```

**Risk:** While parameters are escaped, the column names in `updates` list are constructed dynamically.

**Fix:** Use explicit column mapping:
```python
ALLOWED_UPDATES = {'password_hash', 'salt', 'role'}
for update in updates:
    if update.split(' = ')[0] not in ALLOWED_UPDATES:
        raise ValueError(f"Invalid update field: {update}")
```

#### 🟠 HIGH-03: Pickle Deserialization Vulnerability

**Location:** Multiple files using `pickle.loads()` for embeddings

**Files Affected:**
- `src/core/ai_thread.py` (line 285)
- `src/core/face_recognizer.py` (line 172)
- `src/core/gait_engine.py` (line 300)
- `src/core/reid_engine.py` (line 242)

**Risk:** Pickle deserialization of untrusted data can lead to arbitrary code execution.

**Fix:** Use safer alternatives for numpy arrays:
```python
# Instead of pickle
import numpy as np
import json

def serialize_embedding(embedding: np.ndarray) -> bytes:
    return embedding.tobytes()

def deserialize_embedding(blob: bytes, shape=(256,)) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32).reshape(shape)
```

### 5.3 MEDIUM Severity Issues

#### 🟡 MEDIUM-01: Missing Input Validation in RTSP URLs

**Location:** `src/utils/helpers.py` (lines 384-416)

**Risk:** Malformed or malicious RTSP URLs could cause crashes or security issues.

**Fix:** Add URL validation:
```python
import re

def validate_rtsp_url(url: str) -> bool:
    pattern = r'^rtsp://[a-zA-Z0-9._-]+(?::[a-zA-Z0-9._-]+)?@[a-zA-Z0-9._-]+(?::\d+)?/.+'
    return bool(re.match(pattern, url))
```

#### 🟡 MEDIUM-02: Debug Information in Error Messages

**Location:** Various files returning database errors directly

**Example:** `src/utils/auth_manager.py` (line 193)
```python
return False, f"Database error: {str(e)}"
```

**Risk:** Leaks implementation details to users.

**Fix:** Log full errors internally, return generic messages to users:
```python
logger.error(f"Database error during account creation: {e}")
return False, "An error occurred. Please try again."
```

#### 🟡 MEDIUM-03: No Rate Limiting on Login Attempts

**Current:** 3 attempts then 5-minute lockout per account.

**Risk:** Attackers can try 3 passwords on every username before lockout.

**Fix:** Add IP-based rate limiting or CAPTCHA after failed attempts.

#### 🟡 MEDIUM-04: License File Not Protected

**Location:** `.license` file in application root

**Risk:** Users can copy license files between machines (though validation should fail).

**Fix:** Encrypt license file content with machine-specific key.

### 5.4 LOW Severity Issues

#### 🟢 LOW-01: Sensitive Data in Memory

**Issue:** Face encodings and passwords held in memory without secure wiping.

**Fix:** Use `ctypes` to zero memory after use (complex, low priority).

#### 🟢 LOW-02: Log Files May Contain Sensitive Data

**Location:** `src/utils/logger.py`

**Risk:** Debug logs might contain usernames, paths, etc.

**Fix:** Implement log rotation and consider log sanitization.

#### 🟢 LOW-03: No HTTPS for Telegram API

**Issue:** While Telegram's API uses HTTPS, there's no certificate validation override.

**Assessment:** Generally safe as `requests` handles this properly.

### 5.5 Dependency Vulnerabilities

Run `pip audit` or `safety check` to identify known vulnerabilities:

```bash
pip install pip-audit
pip-audit
```

**Known Concerns:**
- `torch` / `numpy` combinations can have compatibility issues
- Ensure `pillow` is updated (previous versions had image processing CVEs)
- `requests` should be current for SSL improvements

### 5.6 Data Privacy Concerns

| Data Type | Storage | Retention | Risk |
|-----------|---------|-----------|------|
| Face Encodings | SQLite BLOB | Permanent | Contains biometric data |
| Gait Patterns | SQLite BLOB | Permanent | Behavioral biometric |
| Event Snapshots | JPG files | FIFO (configurable) | PII in images |
| Login Credentials | SQLite (hashed) | Permanent | Account security |

**GDPR/Privacy Recommendations:**
1. Implement data export capability for DSAR requests
2. Add bulk deletion for all user-related data
3. Add privacy policy/consent dialog on first run
4. Consider encrypting database at rest
5. Add audit logging for data access

---

## 6. Developer Onboarding

### 6.1 Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10 - 3.12 | Runtime (3.14 has compatibility issues) |
| **Git** | Latest | Version control |
| **Visual Studio Build Tools** | 2019 or later | Required for `dlib` compilation (Windows) |
| **CMake** | 3.20+ | Required for `dlib` |
| **CUDA Toolkit** (optional) | 11.8+ | GPU acceleration |

### 6.2 Environment Setup

#### Windows Setup

```powershell
# 1. Clone repository
git clone https://github.com/yourusername/facepro.git
cd facepro

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install Visual Studio Build Tools (for dlib)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Install "Desktop development with C++"

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Download YOLO model (if not auto-downloaded)
# The model will auto-download on first run, or manually:
# curl -o models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# 6. Run the application
python main.py
```

#### Common Installation Issues

| Issue | Solution |
|-------|----------|
| `dlib` fails to compile | Install Visual Studio Build Tools with C++ workload |
| `torch` CUDA not detected | Install matching CUDA toolkit + cuDNN |
| `face_recognition` import error | Ensure dlib is properly installed first |
| PyQt6 platform plugin error | Install `pyqt6-tools` and set `QT_PLUGIN_PATH` |
| Permission denied on camera | Run as administrator or check antivirus |

### 6.3 Project Structure Quick Reference

```
facepro/
├── main.py                 # Entry point
├── config/
│   ├── settings.json       # App configuration
│   └── cameras.json        # Camera list
├── data/
│   ├── db/facepro.db      # SQLite database
│   ├── faces/             # Enrolled face images
│   └── logs/              # Event snapshots
├── models/                # AI models (yolov8n.pt, etc.)
├── src/
│   ├── core/              # AI/processing engines
│   ├── hardware/          # Telegram, GSM integration
│   ├── ui/                # PyQt6 interface
│   └── utils/             # Helpers, auth, i18n
├── tests/                 # Unit tests
├── docs/                  # Technical documentation
└── build_exe.py           # PyInstaller build script
```

### 6.4 First-Time Run Checklist

1. ✅ Virtual environment activated
2. ✅ All dependencies installed (no errors)
3. ✅ Run `python main.py`
4. ✅ License dialog appears → Use `admin_keygen.py` with shown Machine ID
5. ✅ Setup wizard appears → Create admin account
6. ✅ Login with created credentials
7. ✅ Add a camera (webcam index 0 is easiest)
8. ✅ Start the system and verify video feed

### 6.5 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth_manager.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

### 6.6 Configuration Reference

**`config/settings.json`:**
```json
{
    "telegram": {
        "bot_token": "",      // Telegram bot token
        "chat_id": ""         // Telegram chat/group ID
    },
    "gsm": {
        "enabled": false,
        "com_port": "COM3",
        "baud_rate": 9600,
        "phone_number": ""
    },
    "ai": {
        "motion_threshold": 25,           // Motion sensitivity (0-100)
        "face_confidence_threshold": 0.6, // Face match threshold
        "reid_confidence_threshold": 0.75 // Re-ID match threshold
    },
    "gait": {
        "enabled": true,
        "threshold": 0.70,
        "sequence_length": 30
    },
    "storage": {
        "max_size_gb": 10  // FIFO cleanup threshold
    },
    "ui": {
        "theme": "dark",
        "language": "az"  // "en" or "az"
    }
}
```

---

## 7. Deployment Pipeline & Infrastructure

### 7.1 Build Process

#### Creating Executable

```bash
# 1. Ensure all dependencies are installed
pip install pyinstaller

# 2. Run build script
python build_exe.py

# Output: dist/FacePro/FacePro.exe
```

#### Creating Installer

```bash
# 3. Create Windows installer
python create_setup.py

# Output: FacePro_Setup_v1.0.exe
```

### 7.2 Build Configuration

**`build_exe.py` Summary:**
- Uses PyInstaller `--onedir` mode (faster startup than `--onefile`)
- Includes `src/`, `config/`, face_recognition_models
- Hidden imports for dynamic modules
- Copies YOLO model and creates data directories

**Key PyInstaller Arguments:**
```python
[
    '--name', 'FacePro',
    '--onedir',
    '--windowed',  # No console window
    '--add-data', 'src;src',
    '--add-data', 'config;config',
    '--collect-data', 'face_recognition_models',
    '--hidden-import', 'face_recognition',
]
```

### 7.3 Distribution Structure

```
FacePro_Setup_v1.0.exe
└── Installs to:
    └── C:\Program Files\FacePro\
        ├── FacePro.exe
        ├── config/
        │   ├── settings.json
        │   └── cameras.json
        ├── data/
        │   ├── db/
        │   ├── faces/
        │   └── logs/
        ├── models/
        │   └── yolov8n.pt
        └── _internal/  # Python runtime and dependencies
```

### 7.4 License Key Generation Workflow

1. Customer runs installer, launches FacePro
2. License dialog shows **Machine ID** (e.g., `A1B2-C3D4-E5F6-G7H8`)
3. Customer sends Machine ID to vendor
4. Vendor runs: `python admin_keygen.py A1B2-C3D4-E5F6-G7H8`
5. Vendor sends generated **License Key** to customer
6. Customer enters license key → Activation complete

### 7.5 Update Strategy

**Current:** No auto-update mechanism.

**Recommended Approach:**
1. Version check on startup (optional HTTP call)
2. Notify user of available updates
3. Direct to download page for manual update
4. Consider Squirrel-based auto-updater for future

### 7.6 Infrastructure Requirements

**For End Users:**
- Windows 10/11 (64-bit)
- 4GB RAM minimum (8GB recommended)
- 500MB storage + space for recordings
- Webcam or IP camera access

**For Development:**
- Above requirements
- Python 3.10-3.12
- Visual Studio Build Tools
- ~15GB for full development environment with models

---

## 8. Next Steps & Priority Actions

### 8.1 🔴 IMMEDIATE / Must-Fix Before Scaling

| Priority | Issue | Action | Effort |
|----------|-------|--------|--------|
| **P0** | Telegram credentials exposed | Revoke token, update config, add to gitignore | 30 min |
| **P0** | License salt in source | Implement obfuscation or environment-based salt | 2-4 hours |
| **P1** | Weak password hashing | Migrate to bcrypt | 2-3 hours |
| **P1** | Pickle deserialization | Replace with numpy serialization | 4-6 hours |
| **P2** | SQL injection potential | Add column whitelist validation | 1 hour |

### 8.2 🟠 Short-Term (1-4 weeks)

| Category | Task | Rationale |
|----------|------|-----------|
| **Security** | Implement proper secrets management | Use `python-dotenv` or Windows Credential Manager |
| **Security** | Add comprehensive input validation | Prevent edge cases and potential exploits |
| **Testing** | Increase test coverage to 70%+ | Current coverage is low; add integration tests |
| **Documentation** | Add API documentation | Document internal APIs for future developers |
| **UX** | Add first-run tutorial/wizard | Improve onboarding experience |
| **Logging** | Implement structured logging | Better debugging and audit trail |

### 8.3 🟡 Mid-Term (1-3 months)

| Category | Task | Rationale |
|----------|------|-----------|
| **Performance** | Profile and optimize AI pipeline | Reduce CPU usage, improve FPS |
| **Feature** | Add database encryption | Protect biometric data at rest |
| **Feature** | Implement data export/deletion | GDPR compliance |
| **DevOps** | Set up CI/CD pipeline | Automated testing and builds |
| **Architecture** | Consider moving to separate processes | Better isolation, crash recovery |
| **Scalability** | Add multi-instance support | Run multiple instances for different locations |

### 8.4 🟢 Long-Term (3-6 months)

| Category | Task | Rationale |
|----------|------|-----------|
| **Architecture** | Cloud-optional hybrid deployment | Central management with local processing |
| **Feature** | Mobile companion app | Remote monitoring via Telegram or dedicated app |
| **AI** | Custom model training | Improve accuracy with domain-specific data |
| **Security** | External security audit | Third-party validation |
| **Licensing** | Server-based license validation | Better control and subscription support |
| **Platform** | macOS/Linux support | Current Windows-focused implementation |

### 8.5 Technical Debt Register

| Item | Location | Severity | Effort to Fix |
|------|----------|----------|---------------|
| Hardcoded paths | Various | Medium | 2 hours |
| Inconsistent error handling | Throughout | Medium | 4-6 hours |
| Missing type hints | Older modules | Low | Ongoing |
| Duplicate code in UI | `src/ui/` | Low | 4 hours |
| No migration system for DB | `helpers.py` | Medium | 3-4 hours |
| Missing docstrings | Some modules | Low | Ongoing |

### 8.6 Recommended First Week Actions

1. **Day 1-2:** Fix Critical-01 and Critical-02 (credentials/salt)
2. **Day 3:** Set up development environment, run full test suite
3. **Day 4:** Fix High-01 (password hashing migration)
4. **Day 5:** Review and understand AI pipeline code
5. **Week 2:** Begin tackling High-02 and High-03

### 8.7 Key Contacts & Resources

| Resource | Location |
|----------|----------|
| Source Code | This repository |
| Technical Spec | `docs/TECH_SPEC.md` |
| PRD | `docs/PRD.md` |
| Database Schema | `docs/database_schema.sql` |
| License Spec | `docs/LICENSE_SPEC.md` |
| Admin Key Generator | `admin_keygen.py` |

---

## Appendix A: Database Schema

```sql
-- Users (people to recognize)
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    created_at TIMESTAMP
);

-- Face Encodings (128-dim dlib vectors)
CREATE TABLE face_encodings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    encoding BLOB
);

-- Re-ID Embeddings (1280-dim EfficientNet vectors)
CREATE TABLE reid_embeddings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    vector BLOB,
    confidence REAL,
    captured_at TIMESTAMP
);

-- Gait Embeddings (256-dim ResNet vectors)
CREATE TABLE gait_embeddings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    embedding BLOB,
    confidence REAL,
    captured_at TIMESTAMP
);

-- Event Logs
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_type TEXT,
    object_label TEXT,
    confidence REAL,
    snapshot_path TEXT,
    identification_method TEXT,
    created_at TIMESTAMP
);

-- Application Users (login accounts)
CREATE TABLE app_users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    salt TEXT,
    role TEXT,
    failed_attempts INTEGER,
    is_locked BOOLEAN,
    lock_until TIMESTAMP,
    created_at TIMESTAMP
);
```

---

## Appendix B: Troubleshooting Guide

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Camera not detected | Permissions or driver | Run as admin, update drivers |
| RTSP connection timeout | Firewall or wrong URL | Check firewall, verify URL format |
| Face recognition slow | CPU mode fallback | Verify CUDA installation |
| Memory usage high | Large face database | Optimize embedding storage |
| Telegram not sending | Invalid credentials | Re-test connection in settings |
| License invalid after hardware change | Machine ID changed | Generate new license key |

---

*This document should be treated as confidential and updated as the project evolves.*
