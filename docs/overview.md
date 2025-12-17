# FacePro - Handover Overview Document

**Version:** 1.0.0  
**Date:** December 17, 2025  
**Status:** Production-Ready MVP  

---

## 1. Executive Summary

FacePro is a desktop-based smart security system that transforms existing CCTV/DVR cameras into an intelligent monitoring solution using local AI processing. The system runs entirely offline, making it ideal for security-conscious environments.

### Key Capabilities
- **Face Recognition** - Identify known individuals from enrolled faces (dlib/face_recognition)
- **Person Re-ID** - Track individuals by clothing/body features when face is not visible (EfficientNet-B0)
- **Gait Recognition** - Identify people by walking pattern (ResNet18 silhouette-based)
- **Object Detection** - Detect persons, cats, and dogs (YOLOv8n)
- **Motion Detection** - CPU-efficient gatekeeper to trigger AI only when needed
- **Telegram Notifications** - Real-time alerts with images
- **GSM Fallback** - SMS alerts via USB modem when offline
- **Hardware License Lock** - Prevent unauthorized distribution
- **Multi-language UI** - English, Azerbaijani, Russian with live switching

### Technology Stack
| Component | Technology | Version |
|-----------|------------|---------|
| UI Framework | PyQt6 | 6.10.1 |
| Computer Vision | OpenCV | 4.12.0 |
| Object Detection | YOLOv8 (Ultralytics) | 8.3.x |
| Face Recognition | face_recognition + dlib | 1.3.0 / 20.0.0 |
| Deep Learning | PyTorch | 2.9.1 |
| Database | SQLite | (built-in) |
| Password Hashing | bcrypt | 4.0.0 |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Application                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   UI Layer  │  │  Core Layer │  │   Hardware Layer    │  │
│  │   (PyQt6)   │  │   (AI/CV)   │  │   (GSM/Camera)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Utils     │  │  Database   │  │   Configuration     │  │
│  │  (Helpers)  │  │  (SQLite)   │  │   (JSON files)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Threading Model

```
Main Thread (UI)
    │
    ├── CameraWorker Thread (per camera)
    │       └── Reads frames, emits frame_ready signal
    │
    ├── AIWorker Thread (single)
    │       ├── Loads known faces from DB on start
    │       ├── Processes frames through AI pipeline
    │       └── Emits detection results
    │
    ├── TelegramNotifier Thread (background)
    │       └── Async message queue processing
    │
    └── StorageCleaner Thread (background)
            └── FIFO cleanup on 10-minute interval
```

### 2.3 AI Processing Pipeline

```
Camera Frame
    │
    ▼
Motion Detection (CPU gatekeeper)
    │ (skip if no motion)
    ▼
Object Detection (YOLOv8n)
    │ (filter: person/cat/dog only)
    ▼
Person Detected?
    │
    ├── Yes ──► Face Recognition (dlib)
    │               │
    │               ├── Face Found & Matched ──► Return Name
    │               │       │
    │               │       └── Passive Enrollment (Re-ID + Gait)
    │               │
    │               └── Face Not Found ──► Re-ID Check
    │                                           │
    │                                           ├── Match ──► Return "Name (Re-ID)"
    │                                           │
    │                                           └── No Match ──► Gait Recognition
    │                                                               │
    │                                                               ├── Match ──► Return "Name (Gait)"
    │                                                               │
    │                                                               └── No Match ──► "Unknown"
    │
    └── No ──► Skip
```

### 2.4 Database Schema

```sql
-- users: Basic identity (for face recognition)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- app_users: Application login accounts
CREATE TABLE app_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator',  -- 'admin' or 'operator'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);

-- face_encodings: 128-dim vectors from dlib
CREATE TABLE face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    encoding BLOB NOT NULL,  -- numpy array bytes
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- reid_embeddings: 1280-dim clothing/body vectors
CREATE TABLE reid_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    vector BLOB NOT NULL,
    confidence REAL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- gait_embeddings: 256-dim walking pattern vectors
CREATE TABLE gait_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    confidence REAL DEFAULT 1.0,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- events: Detection history
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    object_label TEXT,
    confidence REAL,
    snapshot_path TEXT,
    identification_method TEXT DEFAULT 'unknown',
    is_sent_telegram BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Module Breakdown

### 3.1 Core Modules (`src/core/`)

| File | Lines | Description |
|------|-------|-------------|
| `ai_thread.py` | ~360 | AIWorker QThread, main processing pipeline |
| `gait_engine.py` | ~327 | GaitEngine - silhouette-based gait recognition |
| `camera_thread.py` | ~283 | CameraWorker, CameraManager for video capture |
| `reid_engine.py` | ~272 | ReIDEngine - EfficientNet-B0 body features |
| `cleaner.py` | ~196 | StorageCleaner - FIFO disk management |
| `face_recognizer.py` | ~188 | FaceRecognizer - dlib face encoding/matching |
| `object_detector.py` | ~124 | ObjectDetector - YOLO wrapper |
| `gait_buffer.py` | ~89 | GaitBufferManager - per-track frame collection |
| `motion_detector.py` | ~74 | MotionDetector - background subtraction |
| `detection.py` | ~34 | Data classes: Detection, DetectionType, FrameResult |
| `gait_types.py` | ~21 | Data classes: GaitBuffer, GaitMatch |

### 3.2 Hardware Modules (`src/hardware/`)

| File | Lines | Description |
|------|-------|-------------|
| `telegram_notifier.py` | ~350 | Telegram Bot API integration, async queue |
| `gsm_modem.py` | ~250 | GSM modem AT commands for SMS |

### 3.3 UI Modules (`src/ui/`)

| File | Description |
|------|-------------|
| `main_window.py` | Main dashboard coordinator (~450 lines) |
| `login_dialog.py` | User authentication dialog |
| `setup_wizard.py` | First-time admin account creation |
| `user_management.py` | User CRUD (Admin only) |
| `change_password.py` | Password change dialog |
| `settings_dialog.py` | Settings UI entry point |
| `license_dialog.py` | License activation UI |
| `video_widget.py` | Video display, VideoGrid |
| `styles.py` | Dark theme CSS |
| `dashboard/` | Modular dashboard components |
| `face_enrollment/` | Face enrollment dialogs |
| `settings/` | Settings tabs (General, AI, Storage, Notifications) |
| `camera_dialogs/` | Camera selection dialogs |

### 3.4 Utility Modules (`src/utils/`)

| File | Description |
|------|-------------|
| `auth_manager.py` | User authentication, session management, bcrypt hashing |
| `license_manager.py` | Hardware-locked license validation |
| `helpers.py` | Image conversion, config I/O, path helpers |
| `i18n.py` | Internationalization (EN, AZ, RU) |
| `logger.py` | Centralized logging (file + console) |

---

## 4. Third-Party Integrations

### 4.1 Telegram Bot API

**Purpose:** Real-time detection alerts with images

**Implementation:**
- File: `src/hardware/telegram_notifier.py`
- Class: `TelegramNotifier`
- Singleton: `get_telegram_notifier()`

**Features:**
- Async message queue (background thread)
- Rate limiting (30s per person, 10s global)
- Auto-retry (3 attempts)
- Photo + caption alerts

**Configuration:**
```json
// config/settings.json
{
    "telegram": {
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    }
}
```

**Environment Variables:** None required (stored in config file)

**Vendor Lock Risk:** LOW - Standard HTTP API, easily replaceable with other messaging services

### 4.2 GSM Modem (SMS)

**Purpose:** Offline fallback alerts when internet is unavailable

**Implementation:**
- File: `src/hardware/gsm_modem.py`
- Class: `GSMModem`
- Singleton: `get_modem()`

**Features:**
- AT command protocol
- Auto COM port detection
- Signal strength check
- Text mode SMS

**Configuration:**
```json
// config/settings.json
{
    "gsm": {
        "enabled": false,
        "com_port": "COM3",
        "baud_rate": 9600,
        "phone_number": "+994501234567"
    }
}
```

**Hardware:** Huawei E3372 (non-HiLink) recommended

**Vendor Lock Risk:** LOW - Standard AT commands, works with any GSM modem

### 4.3 YOLOv8 (Ultralytics)

**Purpose:** Object detection (person, cat, dog)

**Implementation:**
- File: `src/core/object_detector.py`
- Class: `ObjectDetector`
- Model: `yolov8n.pt` (nano, ~6MB)

**Features:**
- Lazy loading (loads on first use)
- YOLO tracking for track_id
- Filtered classes (0=person, 15=cat, 16=dog)

**Model Location:** `models/yolov8n.pt` (auto-downloaded if missing)

**Vendor Lock Risk:** MEDIUM - Ultralytics-specific API, but ONNX export possible

### 4.4 dlib / face_recognition

**Purpose:** Face encoding and matching

**Implementation:**
- File: `src/core/face_recognizer.py`
- Class: `FaceRecognizer`
- Library: `face_recognition` (wrapper around dlib)

**Features:**
- 128-dimensional face encodings
- Tolerance-based matching (default 0.6)
- Database persistence (numpy bytes)

**Installation Note:** Requires Visual Studio Build Tools + CMake for dlib compilation

**Vendor Lock Risk:** LOW - Standard face encoding format, can migrate to other libraries

### 4.5 PyTorch / TorchVision

**Purpose:** Re-ID and Gait recognition neural networks

**Implementation:**
- Re-ID: `src/core/reid_engine.py` (EfficientNet-B0)
- Gait: `src/core/gait_engine.py` (ResNet18 adapted)

**Features:**
- Lazy loading (loads on first use)
- CPU/GPU auto-detection
- L2-normalized embeddings
- Cosine similarity matching

**Model Weights:** Pretrained from TorchVision (auto-downloaded)

**Vendor Lock Risk:** LOW - Standard PyTorch models, ONNX export possible

---

## 5. Security & Vulnerability Audit

### 5.1 Critical Issues (P0 - Fix Immediately)

#### 5.1.1 Telegram Token Exposed in Config
**Location:** `config/settings.json`
**Risk:** HIGH - Token visible in plaintext, can be used to send messages as the bot
**Current State:**
```json
"telegram": {
    "bot_token": "8275886963:AAGrmckSFx20U2Qtiamp-OJf9tZ7ygHYo1M",
    "chat_id": "486493885"
}
```
**Recommendation:**
1. **Immediately rotate the exposed token** via @BotFather
2. Move to environment variable: `FACEPRO_TELEGRAM_TOKEN`
3. Encrypt config file or use OS keychain

#### 5.1.2 License Salt Security (IMPROVED)
**Location:** `src/utils/license_manager.py`
**Current State:** Salt loaded from environment variable or `.license_salt` file
**Risk:** MEDIUM - Salt file may be committed to version control
**Recommendation:**
1. Ensure `.license_salt` is in `.gitignore`
2. Use environment variable `FACEPRO_LICENSE_SALT` in production
3. Consider obfuscation for PyInstaller builds

### 5.2 High Priority Issues (P1)

#### 5.2.1 Password Hashing (FIXED)
**Location:** `src/utils/auth_manager.py`
**Current State:** bcrypt with 12 rounds (secure)
**Previous Issue:** SHA-256 was used (now fixed)
**Status:** ✅ RESOLVED - bcrypt implemented with backward compatibility for legacy SHA-256 hashes

#### 5.2.2 Biometric Data Serialization (IMPROVED)
**Location:** `src/core/gait_engine.py`, `src/core/reid_engine.py`, `src/core/face_recognizer.py`
**Current State:** Using `numpy.tobytes()` / `numpy.frombuffer()` (safe)
**Previous Issue:** pickle was used (arbitrary code execution risk)
**Status:** ✅ RESOLVED - pickle removed, using safe numpy serialization

**Migration Note:** Legacy pickle-format embeddings will fail to load. Run migration script if needed.

#### 5.2.3 No Database Encryption
**Location:** `data/db/facepro.db`
**Risk:** MEDIUM - Biometric data stored in plaintext SQLite
**Recommendation:**
1. Implement SQLCipher for database encryption
2. Or encrypt individual BLOB fields before storage

### 5.3 Medium Priority Issues (P2)

#### 5.3.1 No Audit Logging
**Risk:** MEDIUM - No record of user actions (login, face enrollment, settings changes)
**Recommendation:** Add audit trail table with user_id, action, timestamp, details

#### 5.3.2 No Password Complexity Requirements
**Location:** `src/utils/auth_manager.py`
**Current:** Only minimum length (6 characters)
**Recommendation:** Add requirements for uppercase, lowercase, numbers, special characters

#### 5.3.3 Session Token Not Cryptographically Secure
**Location:** `src/utils/auth_manager.py`
**Current:** Session stored in memory as dataclass
**Recommendation:** Use cryptographically secure session tokens with HMAC validation

### 5.4 Low Priority Issues (P3)

#### 5.4.1 Debug Information in Logs
**Location:** `src/utils/logger.py`
**Risk:** LOW - Debug logs may contain sensitive information
**Recommendation:** Ensure production builds use INFO level, not DEBUG

#### 5.4.2 No Rate Limiting on Login
**Location:** `src/utils/auth_manager.py`
**Current:** Account lockout after 3 attempts (5 min)
**Recommendation:** Add IP-based rate limiting for distributed attacks

---

## 6. Developer Onboarding

### 6.1 Prerequisites

1. **Python 3.10-3.12** (3.12 recommended, 3.14 NOT supported)
2. **Visual Studio Build Tools** with C++ workload (for dlib)
3. **CMake** from cmake.org (add to PATH)
4. **Git** for version control

### 6.2 Installation Steps

```bash
# 1. Clone repository
git clone <repository_url>
cd facepro

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
# Windows:
setx FACEPRO_LICENSE_SALT "your_secret_salt_here"
# Linux/macOS:
export FACEPRO_LICENSE_SALT="your_secret_salt_here"

# 5. Run application
python main.py
```

### 6.3 First Run

1. **License Activation:** Enter license key (generate with `admin_keygen.py`)
2. **Setup Wizard:** Create first admin account
3. **Login:** Authenticate with created credentials
4. **Add Camera:** Settings → Cameras → Add Camera

### 6.4 Development Tools

```bash
# Run tests
pytest tests/

# Run with hypothesis (property-based tests)
pytest tests/test_gait_engine.py -v

# Build executable
python build_exe.py

# Create installer
python create_setup.py

# Generate license key (admin only)
python admin_keygen.py
```

### 6.5 Common Pitfalls

1. **dlib compilation fails:** Ensure VS Build Tools and CMake are installed
2. **CUDA not detected:** PyTorch defaults to CPU, which is fine for development
3. **Camera not opening:** Check if another application is using the camera
4. **RTSP timeout:** Ensure camera and PC are on the same network
5. **face_recognition import error:** Reinstall with `pip install face_recognition --no-cache-dir`

### 6.6 Project Structure

```
FacePro/
├── main.py              # Entry point (license → login → dashboard)
├── admin_keygen.py      # License key generator (ADMIN ONLY)
├── requirements.txt     # Python dependencies
├── config/
│   ├── settings.json    # App configuration
│   └── cameras.json     # Camera list
├── data/
│   ├── db/facepro.db    # SQLite database
│   ├── faces/           # Enrolled face images
│   └── logs/            # Event snapshots
├── models/              # AI model files
├── src/
│   ├── core/            # AI & processing
│   ├── hardware/        # GSM, Telegram
│   ├── ui/              # PyQt6 interface
│   └── utils/           # Helpers, auth, i18n
├── tests/               # Test files
├── docs/                # Documentation
└── memory-bank/         # AI context preservation
```

---

## 7. Deployment & Infrastructure

### 7.1 Build Process

```bash
# 1. Build executable (PyInstaller)
python build_exe.py
# Output: dist/FacePro/

# 2. Create installer
python create_setup.py
# Output: FacePro_Setup.exe
```

### 7.2 Packaging Contents

The installer includes:
- Main executable (`FacePro.exe`)
- Python runtime (embedded)
- All dependencies (PyQt6, OpenCV, PyTorch, etc.)
- AI models (`yolov8n.pt`)
- Default configuration files
- Empty data directories

### 7.3 License System

**Flow:**
1. App generates Machine ID (SHA-256 of CPU + Motherboard + Volume Serial)
2. Admin generates License Key using `admin_keygen.py` with Machine ID
3. User enters License Key in activation dialog
4. App validates Key against Machine ID
5. Valid key saved to `.license` file (hidden)

**Anti-Piracy:**
- Hardware-locked (key invalid on different machine)
- Salt required for key generation (not in source code)

### 7.4 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Intel i5 6th Gen | Intel i7 / Apple Silicon |
| RAM | 4GB | 8GB+ |
| Storage | 10GB | 50GB+ |
| OS | Windows 10 | Windows 11 |
| GPU | Not required | NVIDIA (optional) |

### 7.5 Network Requirements

- **Telegram:** Outbound HTTPS (port 443) to api.telegram.org
- **RTSP Cameras:** Local network access (port 554)
- **GSM Modem:** USB connection, no network required

---

## 8. Next Steps & Priority Actions

### 8.1 MUST-FIX Before Scaling (Critical)

| Priority | Issue | Action | Effort |
|----------|-------|--------|--------|
| P0 | Telegram token exposed | Rotate token, move to env var | 1 hour |
| P0 | Config file unencrypted | Encrypt sensitive fields | 4 hours |
| P1 | No database encryption | Implement SQLCipher | 8 hours |
| P1 | No audit logging | Add audit trail table | 4 hours |

### 8.2 Short-Term (1-2 weeks)

1. **RTSP Camera Testing** - Test with real Hikvision/Dahua cameras
2. **Password Complexity** - Add requirements for strong passwords
3. **Error Recovery** - Improve handling of camera disconnections
4. **Unit Test Coverage** - Increase to 70%+ (currently ~30%)
5. **Documentation** - Create user manual PDF

### 8.3 Mid-Term (1-2 months)

1. **GPU Acceleration** - Enable CUDA for faster inference
2. **Multi-Camera Grid** - Support 4+ simultaneous cameras
3. **Visual ROI Editor** - Draw zones on video preview
4. **Event Search** - Filter events by date, person, camera
5. **Database Backup/Restore** - Export/import functionality
6. **Auto-Update Mechanism** - Check for and install updates

### 8.4 Long-Term (3-6 months)

1. **Cloud Connector** - Optional remote monitoring
2. **Mobile App** - iOS/Android companion app
3. **Analytics Dashboard** - Detection statistics, trends
4. **Multi-User Roles** - More granular permissions
5. **Plugin System** - Extensible detection modules
6. **Cross-Platform** - macOS and Linux support

---

## 9. Configuration Reference

### 9.1 settings.json

```json
{
    "app_name": "FacePro",
    "version": "1.0.0",
    "telegram": {
        "bot_token": "",      // Get from @BotFather
        "chat_id": ""         // Get from @userinfobot
    },
    "gsm": {
        "enabled": false,
        "com_port": "COM3",
        "baud_rate": 9600,
        "phone_number": ""
    },
    "ai": {
        "motion_threshold": 25,           // 0-100, higher = less sensitive
        "face_confidence_threshold": 0.6, // 0-1, lower = more matches
        "reid_confidence_threshold": 0.75,
        "detection_classes": ["person", "cat", "dog"]
    },
    "gait": {
        "enabled": true,
        "threshold": 0.7,        // 0.5-0.95
        "sequence_length": 30    // 20-60 frames
    },
    "storage": {
        "max_size_gb": 10,
        "recordings_path": "./data/logs/",
        "faces_path": "./data/faces/",
        "fifo_check_interval_minutes": 10
    },
    "camera": {
        "reconnect_interval_seconds": 5,
        "target_fps": 30,
        "frame_skip": 5
    },
    "ui": {
        "theme": "dark",
        "language": "en"  // en, az, ru
    }
}
```

### 9.2 cameras.json

```json
{
    "cameras": [
        {
            "name": "Front Door",
            "source": "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
            "type": "RTSP (IP Camera)",
            "roi_points": []
        },
        {
            "name": "Webcam",
            "source": "0",
            "type": "Webcam",
            "roi_points": []
        }
    ]
}
```

### 9.3 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FACEPRO_LICENSE_SALT` | Yes | Secret salt for license key generation |
| `FACEPRO_TELEGRAM_TOKEN` | No | Telegram bot token (alternative to config) |
| `OPENCV_LOG_LEVEL` | No | Set to "SILENT" to suppress OpenCV logs |

---

## 10. Contact & Support

**Original Developer:** NurMurDev  
**Project Start:** December 2025  
**License:** Proprietary (Hardware-locked)

For technical questions, refer to:
- `memory-bank/` - AI context preservation files
- `docs/PRD.md` - Product requirements
- `docs/TECH_SPEC.md` - Technical specification
- `docs/LICENSE_SPEC.md` - License system specification

---

*Document generated: December 17, 2025*
