# FacePro - System Patterns

## Architecture Overview

### High-Level Architecture
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

### Threading Model
```
Main Thread (UI)
    │
    ├── CameraWorker Thread (per camera)
    │       └── Reads frames, emits frame_ready signal
    │
    ├── AIWorker Thread (single)
    │       ├── Loads known faces from DB on start
    │       └── Processes frames, emits detection results
    │
    └── StorageCleaner Thread (background)
            └── FIFO cleanup on interval
```

### Deployment & Licensing
- **Packaging:**
    - Use `PyInstaller` (One-Dir mode) to collect dependencies.
    - Use `create_setup.py` (Custom Python Script) to zip payload and create a self-extracting installer GUI.
- **Licensing:**
    - Hardware-locked (CPU + MB + UUID).
    - Checks on startup (`main.py`).
    - Admin Keygen (`admin_keygen.py`) generates keys based on client Machine ID.
- **Path Management:**
    - Use `src/utils/helpers.py:get_app_root()` to determine runtime environment (Source vs Frozen).
    - Use `get_db_path()` to ensure database portability.
    - Auto-initialize database schema if missing (Self-Healing).

### UI Modular Architecture
```
src/ui/
├── main_window.py          # Coordinator (~350 lines)
│   └── Manages system state, signals, tray, auth
│
├── login_dialog.py         # User authentication (NEW)
├── setup_wizard.py         # First-time admin setup (NEW)
├── user_management.py      # User CRUD - Admin only (NEW)
├── change_password.py      # Password change dialog (NEW)
│
└── dashboard/              # Component Modules
    ├── __init__.py         # Exports all components
    ├── widgets.py          # ActivityItem, ActionCard
    ├── sidebar.py          # SidebarWidget (profile, nav, stats, role-based)
    ├── home_page.py        # HomePage (welcome, cards, activity)
    ├── camera_page.py      # CameraPage (video grid, controls)
    └── logs_page.py        # LogsPage (filters, export)
```

**Benefits:**
- Single Responsibility Principle
- Easier testing and maintenance
- Parallel development possible
- `main_window.py` reduced from 730→350 lines

### User Authentication Architecture (NEW)
```
┌─────────────────────────────────────────────────────────────┐
│                    Authentication Flow                        │
├─────────────────────────────────────────────────────────────┤
│  App Start                                                    │
│      │                                                        │
│      ▼                                                        │
│  ┌─────────────────┐    No Users    ┌──────────────────┐    │
│  │  Check DB for   │ ─────────────► │  SetupWizard     │    │
│  │  existing users │                │  (Create Admin)  │    │
│  └─────────────────┘                └──────────────────┘    │
│      │ Has Users                            │               │
│      ▼                                      ▼               │
│  ┌─────────────────┐                ┌──────────────────┐    │
│  │  LoginDialog    │ ◄───────────── │  First Admin     │    │
│  │  (Authenticate) │                │  Created         │    │
│  └─────────────────┘                └──────────────────┘    │
│      │ Success                                              │
│      ▼                                                      │
│  ┌─────────────────┐                                        │
│  │  MainWindow     │ ◄── Role-based UI applied              │
│  │  (Dashboard)    │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

### Role-Based Access Control (NEW)
```
┌─────────────────────────────────────────────────────────────┐
│                    Role Permissions                          │
├─────────────────────────────────────────────────────────────┤
│  Feature              │  Admin  │  Operator                 │
│  ─────────────────────┼─────────┼───────────                │
│  Camera Monitoring    │   ✅    │    ✅                     │
│  Event Logs           │   ✅    │    ✅                     │
│  Change Password      │   ✅    │    ✅                     │
│  Settings             │   ✅    │    ❌                     │
│  User Management      │   ✅    │    ❌                     │
│  Face Enrollment      │   ✅    │    ❌                     │
└─────────────────────────────────────────────────────────────┘

Implementation: sidebar.set_user_info(username, role)
  - Hides buttons based on role
  - Admin sees all, Operator sees limited
```

## Refactoring Targets (from Handover Audit)
- Consolidate all database operations into `DatabaseManager` class (currently scattered/helper-based).
- Move UI-specific business logic (like enrollment) fully into Controllers or Services.
- **Security:** Move license salt to environment variable
- **Security:** Migrate password hashing from SHA-256 to bcrypt
- **Security:** Replace pickle with numpy serialization for biometric data
- **Security:** Implement SQLCipher for database encryption

## Documentation
- **Handover Document:** `docs/HANDOVER_OVERVIEW.md` (581 lines)
  - Complete system architecture
  - Module breakdown with line counts
  - Third-party integration analysis
  - Security audit (11 issues identified)
  - Developer onboarding guide
  - Priority action items

## Key Design Patterns

### 1. Singleton Pattern
Used for global managers that should have only one instance:
- `FaceProLogger` - Centralized logging
- `StorageCleaner` - Single cleanup manager
- `ReIDEngine` - Single model instance
- `GSMModem` - Single modem connection

### 2. Observer Pattern (Qt Signals/Slots)
Used for thread-safe communication:
- `CameraWorker.frame_ready` → `AIWorker.process_frame`
- `AIWorker.frame_processed` → `MainWindow.update_display`
- `AIWorker.detection_alert` → `MainWindow.add_event`
- `FaceEnrollmentDialog.face_enrolled` → `MainWindow._on_face_enrolled`

### 3. Lazy Loading Pattern
Used for expensive initializations:
- YOLO model loads on first detection
- PyTorch loads when Re-ID is first used
- face_recognition loads on first face check

### 4. Strategy Pattern
Used for camera URL generation:
- Hikvision URL template
- Dahua URL template
- Generic URL template

## Component Relationships

### UI Components
```
MainWindow
├── VideoGrid
│   └── VideoWidget (per camera)
├── EventsPanel
│   └── EventListItem (per event)
├── StatusPanel
│   └── StatusIndicator
├── SettingsDialog
│   ├── GeneralTab
│   ├── CamerasTab
│   ├── AITab
│   ├── NotificationsTab
│   └── StorageTab
├── FaceEnrollmentDialog      # NEW
│   └── FacePreviewWidget
└── ManageFacesDialog         # NEW
```

### Core Components (Modularized)
```
src/core/
├── detection.py           # Data classes
│   ├── DetectionType      # Enum: PERSON, CAT, DOG, UNKNOWN
│   ├── Detection          # Single detection result
│   └── FrameResult        # Frame processing result
│
├── motion_detector.py     # CPU gatekeeper
│   └── MotionDetector     # Background subtraction
│
├── object_detector.py     # YOLO wrapper
│   └── ObjectDetector     # Person/Cat/Dog detection
│
├── face_recognizer.py     # dlib wrapper
│   └── FaceRecognizer     # Face encoding & matching
│
├── ai_thread.py           # Main pipeline
│   ├── AIWorker           # QThread for AI processing
│   └── draw_detections()  # Bounding box drawing
│
├── gait_types.py          # Gait data classes
│   ├── GaitBuffer         # Per-track silhouette buffer
│   └── GaitMatch          # Gait match result
│
├── gait_buffer.py         # Buffer management
│   └── GaitBufferManager  # Track-based frame collection
│
├── gait_engine.py         # Gait recognition
│   └── GaitEngine         # Silhouette → Embedding → Match
│
├── reid_engine.py         # Re-ID
│   └── ReIDEngine         # Body feature extraction
│
└── camera_thread.py       # Video capture
    ├── CameraWorker       # Per-camera QThread
    └── CameraManager      # Multi-camera coordinator
```

## Critical Implementation Paths

### Frame Processing Pipeline
1. CameraWorker reads frame from source
2. Frame emitted to AIWorker via signal
3. AIWorker checks motion (skip if none)
4. AIWorker runs YOLO detection
5. For each person: face recognition → Re-ID fallback
6. Results emitted to UI
7. Alerts triggered for unknown persons

### License Validation Flow
1. App starts, calls `check_license()`
2. If `.license` file exists, validate against Machine ID
3. If valid, proceed to GUI
4. If invalid/missing, show Machine ID, prompt for key
5. On valid key entry, save to `.license`, proceed to GUI

### Face Enrollment Flow (NEW)
1. User selects Faces → Add Known Face
2. FaceEnrollmentDialog opens
3. User browses image or captures from webcam
4. System validates: exactly 1 face required
5. On Save:
   - Extract face encoding (128-dim vector)
   - Check if user exists in DB (by name)
   - Insert/Update user record
   - Insert face_encodings record (pickle blob)
6. Signal emitted to MainWindow
7. If AIWorker running, add face to live recognizer

### Face Recognition Flow
1. AIWorker starts → `load_from_database()` called
2. All encodings loaded: users JOIN face_encodings
3. Pickle deserialize → numpy arrays in dict
4. On each frame with person detection:
   - Extract crop from bbox
   - Get face encoding if face visible
   - Compare against all known encodings
   - Return match if distance < tolerance

### Gait Recognition Flow (NEW)
```
Person Detected → Face Recognition
                        ↓
              ┌─────────┴─────────┐
              │ Success           │ Fail
              ↓                   ↓
    Passive Gait Enrollment    Re-ID Check
    (extract silhouette,            ↓
     add to buffer,           ┌─────┴─────┐
     save when 30 frames)     │ Success   │ Fail
                              ↓           ↓
                           Label      Gait Recognition
                                          ↓
                                    ┌─────┴─────┐
                                    │ Match     │ No Match
                                    ↓           ↓
                              "Name (Gait)"  "Unknown"
```

### Gait Recognition Components
1. **GaitEngine** - Core recognition engine (singleton)
   - Silhouette extraction (64x64 binary)
   - Embedding extraction (256D via ResNet18)
   - Cosine similarity matching
   - Database operations

2. **GaitBufferManager** - Per-track frame buffer
   - Collects 30 silhouettes per track_id
   - 5 second timeout for stale buffers
   - Isolated buffers per person

3. **Passive Enrollment** - Auto-learning
   - When face recognized, extract silhouette
   - Add to buffer, save embedding when full
   - Max 10 embeddings per user (FIFO)

### Configuration Persistence
1. Settings saved to `config/settings.json`
2. Cameras saved to `config/cameras.json`
3. Loaded at startup, merged with defaults
4. Changes applied immediately via signals

## Database Schema
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
    encoding BLOB NOT NULL,  -- pickle(numpy array)
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- reid_embeddings: clothing/body vectors
CREATE TABLE reid_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    vector BLOB NOT NULL,
    confidence REAL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- gait_embeddings: Walking pattern vectors (NEW)
CREATE TABLE gait_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,   -- pickle(256D numpy array)
    confidence REAL DEFAULT 1.0,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
-- Index: idx_gait_user ON gait_embeddings(user_id)

-- events: Detection history
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    object_label TEXT,
    confidence REAL,
    snapshot_path TEXT,
    identification_method TEXT DEFAULT 'unknown',  -- 'face', 'reid', 'gait', 'unknown' (NEW)
    is_sent_telegram BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Key Data Flows

### Encoding Storage
```
Image (BGR) → RGB → face_recognition.face_encodings()
    → numpy.ndarray (128,) → pickle.dumps() → BLOB
```

### Encoding Retrieval
```
BLOB → pickle.loads() → numpy.ndarray (128,)
    → dict[name: list[encodings]]
```

### Face Matching
```
Live encoding → face_recognition.face_distance(known, live)
    → distance float → if < 0.6: MATCH
```

### User Authentication Flow (NEW)
```
Login Request → AuthManager.login(username, password)
    │
    ├── Check account exists
    ├── Check account not locked
    ├── Verify password (SHA-256 + salt)
    │
    ├── Success: Create session, reset failed_attempts
    └── Failure: Increment failed_attempts, lock if >= 3
```

### Password Hashing (NEW)
```
Password + Random Salt → SHA-256 → password_hash
Storage: (password_hash, salt) in app_users table
Verification: SHA-256(input + stored_salt) == stored_hash
```

### Session Management (NEW)
```
AuthManager (Singleton)
├── _current_user: UserSession | None
├── _session_start: datetime
├── login() → creates session
├── logout() → clears session, emits signal
├── is_logged_in() → bool
├── get_current_user() → UserSession
└── check_session_timeout() → auto-logout if expired
```
