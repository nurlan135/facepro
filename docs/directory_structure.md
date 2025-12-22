# Project Directory Structure

**Last Updated:** 2025-12-22

```
FacePro/
├── assets/                 # Icons (.ico), logo.png, UI styles (.qss)
├── config/
│   ├── settings.json       # App config (Telegram token, threshold, paths)
│   └── cameras.json        # Saved camera list (RTSP URLs)
├── data/
│   ├── db/
│   │   └── facepro.db      # SQLite Database (Metadata)
│   ├── faces/              # Registered user reference images (jpg)
│   │   ├── Nurlan/         # Per-user face folders
│   │   └── Ramil/
│   └── logs/               # Event snapshots (saved detections)
├── models/
│   └── yolov8n.pt          # Object Detection weights (YOLOv8 nano)
│   # Note: InsightFace models auto-download to ~/.insightface/
├── src/
│   ├── core/               # AI & Processing (MODULARIZED)
│   │   ├── __init__.py     # Exports all components
│   │   ├── detection.py    # DetectionType, Detection, FrameResult
│   │   ├── motion_detector.py  # MotionDetector class
│   │   ├── object_detector.py  # ObjectDetector (YOLO)
│   │   ├── face_recognizer.py  # FaceRecognizer (InsightFace/dlib)
│   │   ├── ai_thread.py    # AIWorker, draw_detections
│   │   ├── storage_worker.py   # StorageWorker (async DB/disk I/O)
│   │   ├── gait_types.py   # GaitBuffer, GaitMatch
│   │   ├── gait_buffer.py  # GaitBufferManager
│   │   ├── gait_engine.py  # GaitEngine (silhouette-based)
│   │   ├── reid_engine.py  # ReIDEngine (body features)
│   │   ├── camera_thread.py    # CameraWorker, CameraManager
│   │   ├── cleaner.py      # FIFO Storage Manager
│   │   ├── detectors/      # Face Detection Backends (NEW 2025-12-22)
│   │   │   ├── __init__.py
│   │   │   └── insightface_adapter.py  # InsightFace ONNX wrapper
│   │   ├── database/       # Database Access Layer (DAL)
│   │   │   ├── db_manager.py   # DatabaseManager singleton
│   │   │   └── repositories/   # Repository pattern
│   │   │       ├── app_user_repository.py
│   │   │       ├── embedding_repository.py
│   │   │       ├── event_repository.py
│   │   │       └── user_repository.py
│   │   └── services/       # Business Logic Services (NEW 2025-12-22)
│   │       ├── __init__.py
│   │       ├── detection_service.py    # Motion + YOLO
│   │       ├── recognition_service.py  # Face + Re-ID + Gait
│   │       └── matching_service.py     # In-memory vector matching
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── gsm_modem.py    # Serial AT Commands wrapper
│   │   └── telegram_notifier.py # Telegram Bot Integration
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py  # Main Dashboard (Coordinator)
│   │   ├── video_widget.py # Custom PyQt Label for Video
│   │   ├── settings_dialog.py
│   │   ├── license_dialog.py  # License activation
│   │   ├── zone_editor.py  # ROI zone editor
│   │   ├── styles.py       # Dark theme
│   │   ├── login_dialog.py # User login UI
│   │   ├── setup_wizard.py # First-time setup
│   │   ├── user_management.py # User CRUD (Admin only)
│   │   ├── change_password.py # Password change dialog
│   │   ├── camera_preview.py # Camera preview thread & card
│   │   ├── camera_dialogs/  # Camera Dialogs (MODULARIZED)
│   │   │   ├── __init__.py
│   │   │   ├── local_camera_selector.py
│   │   │   └── rtsp_config_dialog.py
│   │   ├── face_enrollment/ # Face Enrollment (Modular)
│   │   │   ├── __init__.py
│   │   │   ├── enrollment_dialog.py
│   │   │   ├── manage_dialog.py
│   │   │   └── widgets.py
│   │   ├── settings/        # Settings (Modular)
│   │   │   ├── __init__.py
│   │   │   ├── settings_dialog.py
│   │   │   ├── dialogs/
│   │   │   │   ├── camera_dialog.py
│   │   │   │   └── camera_type_selector.py
│   │   │   └── tabs/
│   │   │       ├── ai_tab.py
│   │   │       ├── cameras_tab.py
│   │   │       ├── general_tab.py
│   │   │       ├── notifications_tab.py
│   │   │       └── storage_tab.py
│   │   └── dashboard/       # Dashboard Components (Modular)
│   │       ├── __init__.py
│   │       ├── widgets.py   # ActivityItem, ActionCard
│   │       ├── sidebar.py   # SidebarWidget
│   │       ├── home_page.py # HomePage (welcome, cards)
│   │       ├── camera_page.py # CameraPage (video grid)
│   │       └── logs_page.py # LogsPage (filters, export)
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py      # Image conversion, config, paths
│       ├── logger.py       # Centralized logging
│       ├── i18n.py         # Internationalization (EN, AZ, RU)
│       ├── license_manager.py # Hardware-locked licensing
│       └── auth_manager.py # User authentication (bcrypt)
├── scripts/                # Utility Scripts
│   ├── migrate_embeddings.py   # Legacy pickle → numpy migration
│   └── verify_recognition.py   # Recognition verification
├── tests/
│   ├── __init__.py
│   ├── test_gait_engine.py     # Gait engine tests (hypothesis)
│   ├── test_auth_manager.py    # Auth manager tests
│   ├── test_recognition_accuracy.py  # InsightFace accuracy test (NEW)
│   └── benchmark_recognition.py      # dlib vs InsightFace benchmark
├── docs/
│   ├── PRD.md              # Product requirements
│   ├── TECH_SPEC.md        # Technical specification
│   ├── LICENSE_SPEC.md     # License system spec
│   ├── database_schema.sql # SQLite schema
│   ├── directory_structure.md # This file
│   ├── overview.md         # System overview & handover
│   └── requirements.txt    # Docs-specific requirements
├── plans/                  # Development Plans
│   └── backend_optimization.md
├── main.py                 # Application Entry Point
├── generate_key_standalone.py  # License key generator (ADMIN)
├── installer_gui.py        # Installer GUI (Tkinter)
├── process_icons.py        # Icon processing script
├── requirements.txt        # Python dependencies
├── README.md
└── AGENTS.md               # AI Agent instructions
```

## Key Architecture Changes (2025-12-22)

### 1. InsightFace Migration
- **Old:** `dlib` + `face_recognition` (128d vectors, requires C++ compiler)
- **New:** `insightface` + `onnxruntime` (512d vectors, ~6x faster)
- **Adapter:** `src/core/detectors/insightface_adapter.py`

### 2. Service Layer
New business logic services in `src/core/services/`:
| Service | Responsibility |
|---------|---------------|
| `DetectionService` | Motion detection + YOLO object detection |
| `RecognitionService` | Face, Re-ID, and Gait recognition |
| `MatchingService` | In-memory vector similarity matching |

### 3. Database Access Layer (DAL)
Repository pattern in `src/core/database/repositories/`:
- `UserRepository` - Known person CRUD
- `EmbeddingRepository` - Face/Re-ID/Gait vectors
- `EventRepository` - Detection events
- `AppUserRepository` - Login user management

### 4. Async Storage
`StorageWorker` handles all disk I/O asynchronously:
- Snapshot saving
- Database insertions
- Embedding storage

## Module Statistics (2025-12-22)

### src/core/ Line Counts
| File | Lines | Description |
|------|-------|-------------|
| ai_thread.py | ~400 | AIWorker orchestrator |
| face_recognizer.py | ~340 | Multi-backend face rec |
| gait_engine.py | ~330 | Gait pattern recognition |
| camera_thread.py | ~290 | Video capture & reconnect |
| reid_engine.py | ~280 | Body/clothing Re-ID |
| storage_worker.py | ~200 | Async I/O worker |
| cleaner.py | ~200 | FIFO storage cleanup |
| object_detector.py | ~130 | YOLO wrapper |
| insightface_adapter.py | ~120 | InsightFace wrapper |

### Threading Model
```
┌─────────────────────────────────────────────────────────┐
│                    Main Thread (UI)                      │
│  PyQt6 Event Loop, Button Clicks, Display               │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌───────────────┐ ┌───────────┐ ┌───────────────┐
│ CameraWorker  │ │ AIWorker  │ │ StorageWorker │
│ (per camera)  │ │           │ │               │
│ RTSP/Webcam   │ │ Detection │ │ DB + Disk I/O │
│ Frame capture │ │ Recognition│ │ Async writes  │
└───────────────┘ └───────────┘ └───────────────┘
```
