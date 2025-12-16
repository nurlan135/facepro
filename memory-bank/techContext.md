# FacePro - Technical Context

## Technology Stack

### Core Technologies
| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| UI Framework | PyQt6 | 6.10.1 | Cross-platform desktop GUI |
| Computer Vision | OpenCV | 4.12.0 | Video capture, image processing |
| Object Detection | YOLOv8 (Ultralytics) | 8.3.x | Person/Cat/Dog detection |
| Face Recognition | face_recognition + dlib | 1.3.0 / 20.0.0 | Face encoding & matching |
| Deep Learning | PyTorch | 2.9.1 | Re-ID model inference |
| Database | SQLite | (built-in) | Local data storage |

### Supporting Libraries
| Library | Purpose |
|---------|---------|
| numpy | Array operations |
| Pillow | Image handling |
| pyserial | GSM modem communication |
| requests | HTTP requests (Telegram) |
| psutil | System monitoring |
| schedule | Background task scheduling |
| pickle | Serializing face encodings |

## Development Setup

### Prerequisites
1. Python 3.12 (recommended)
2. Visual Studio Build Tools with C++ (for dlib compilation)
3. CMake from cmake.org (add to PATH)
4. VC++ Redistributable (for PyTorch)

### Installation Steps
python main.py
```

### Project Structure
```
FacePro/
├── main.py              # Entry point with license check
├── admin_keygen.py      # License key generator (ADMIN ONLY)
├── requirements.txt
├── README.md
├── AGENTS.md            # Memory Bank instructions
├── .license             # Generated license file (hidden)
│
├── config/
│   ├── settings.json    # App configuration
│   └── cameras.json     # Camera list
│
├── data/
│   ├── db/
│   │   ├── faceguard.db # SQLite database
│   │   └── init_db.py   # DB initialization
│   ├── faces/           # Enrolled face images
│   └── logs/            # Event snapshots
│
├── docs/
│   ├── PRD.md           # Product requirements
│   ├── TECH_SPEC.md     # Technical specification
│   ├── LICENSE_SPEC.md  # License system spec
│   └── database_schema.sql
│
├── memory-bank/         # AI context preservation
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   ├── activeContext.md
│   └── progress.md
│
├── models/              # AI model files (downloaded at runtime)
│
└── src/
    ├── core/
    │   ├── ai_thread.py      # AI processing pipeline
    │   ├── camera_thread.py  # Video capture
    │   ├── cleaner.py        # FIFO storage manager
    │   └── reid_engine.py    # Person Re-ID
    │
    ├── hardware/
    │   ├── gsm_modem.py      # SMS via AT commands
    │   └── telegram_notifier.py # Telegram notifications
    │
    ├── ui/
    │   ├── main_window.py    # Main dashboard coordinator
    │   ├── video_widget.py   # Video display, VideoGrid
    │   ├── settings_dialog.py # Settings UI
    │   ├── face_enrollment.py # Face enrollment dialogs
    │   ├── license_dialog.py  # License activation UI
    │   ├── zone_editor.py     # ROI zone editing
    │   ├── styles.py         # Dark theme
    │   ├── login_dialog.py   # User login UI (NEW)
    │   ├── setup_wizard.py   # First-time setup (NEW)
    │   ├── user_management.py # User CRUD - Admin only (NEW)
    │   ├── change_password.py # Password change dialog (NEW)
    │   └── dashboard/        # Modular UI components
    │       ├── __init__.py
    │       ├── widgets.py    # ActivityItem, ActionCard
    │       ├── sidebar.py    # SidebarWidget (role-based visibility)
    │       ├── home_page.py  # HomePage
    │       ├── camera_page.py # CameraPage
    │       └── logs_page.py  # LogsPage with filters
    │
    └── utils/
        ├── logger.py         # Centralized logging
        ├── helpers.py        # Utility functions
        ├── license_manager.py # License validation
        ├── auth_manager.py   # User authentication (NEW)
        └── i18n.py           # Internationalization (EN, AZ, RU)
```

## Technical Constraints

### Performance Requirements
- **Target FPS**: 30 fps per camera
- **Detection latency**: < 500ms
- **Memory usage**: < 2GB (4 cameras)
- **CPU usage**: < 50% on i5 6th gen

### Hardware Requirements
- **Minimum CPU**: Intel i5 6th Gen / AMD equivalent
- **Minimum RAM**: 4GB (8GB recommended)
- **GPU**: Not required (CPU inference)
- **Storage**: 10GB+ for recordings

### Compatibility
- **OS**: Windows 10/11 (primary), macOS/Linux (untested)
- **Cameras**: Any RTSP-compatible (Hikvision, Dahua, generic)
- **Webcams**: USB webcams (index 0, 1, 2...)

## Database Schema Details

### users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**Note**: No `role` column - removed for simplicity

### face_encodings Table
```sql
CREATE TABLE face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    encoding BLOB NOT NULL,  -- pickle(numpy.ndarray)
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
```
**Note**: No `image_path` column - images stored in data/faces/ separately

### Encoding Storage Format
- 128-dimensional numpy float64 array
- Serialized with pickle.dumps()
- Deserialized with pickle.loads()
- Example size: ~1.2KB per encoding

## Dependencies (requirements.txt)
```
PyQt6>=6.4.0
opencv-python>=4.8.0
Pillow>=9.5.0
ultralytics>=8.0.0
torch>=2.0.0
torchvision>=0.15.0
face_recognition>=1.3.0
dlib>=19.24.0
numpy>=1.24.0
pyserial>=3.5
requests>=2.31.0
schedule>=1.2.0
psutil>=5.9.0
```

## Tool Usage Patterns

### Logging
All modules use centralized logger:
```python
from src.utils.logger import get_logger
logger = get_logger()
logger.info("Message")
```

### Configuration
```python
from src.utils.helpers import load_config, save_config
config = load_config()  # loads settings.json
save_config(config)     # saves settings.json
```

### Thread-safe Frame Processing
```python
# Emit from worker thread
self.frame_ready.emit(frame, camera_name)

# Receive in main thread
@pyqtSlot(np.ndarray, str)
def on_frame(self, frame, name):
    ...
```

### Face Encoding Storage
```python
import pickle
import sqlite3

# Save
encoding_blob = pickle.dumps(encoding_array)
cursor.execute("INSERT INTO face_encodings (user_id, encoding) VALUES (?, ?)", 
               (user_id, encoding_blob))

# Load
cursor.execute("SELECT encoding FROM face_encodings WHERE user_id = ?", (user_id,))
encoding_array = pickle.loads(cursor.fetchone()[0])
```

### License Validation
```python
from src.utils.license_manager import check_license, activate_license

is_valid, message = check_license()
if not is_valid:
    success, msg = activate_license(user_input_key)
```
