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

### Core Components
```
AIWorker
├── MotionDetector (gatekeeper)
├── ObjectDetector (YOLO)
├── FaceRecognizer (dlib/face_recognition)
│   ├── load_from_database()  # NEW
│   └── _known_encodings dict
└── ReIDEngine (EfficientNet-B0)

CameraManager
└── CameraWorker (per camera)
    └── cv2.VideoCapture
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

### Configuration Persistence
1. Settings saved to `config/settings.json`
2. Cameras saved to `config/cameras.json`
3. Loaded at startup, merged with defaults
4. Changes applied immediately via signals

## Database Schema
```sql
-- users: Basic identity
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- face_encodings: 128-dim vectors from dlib
CREATE TABLE face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    encoding BLOB NOT NULL,  -- pickle(numpy array)
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- reid_embeddings: Future - clothing/body vectors
CREATE TABLE reid_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    vector BLOB NOT NULL,
    confidence REAL,
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
