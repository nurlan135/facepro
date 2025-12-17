# Project Directory Structure

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
│   └── logs/               # Event snapshots (saved detections)
├── models/
│   ├── yolov8n.pt          # Object Detection weights (YOLOv8 nano)
│   └── efficientnet_b0.pth # Re-ID Feature Extractor (optional)
│   # Note: dlib face model is auto-downloaded by face_recognition library
├── src/
│   ├── core/               # AI & Processing (MODULARIZED)
│   │   ├── __init__.py     # Exports all components
│   │   ├── detection.py    # DetectionType, Detection, FrameResult
│   │   ├── motion_detector.py  # MotionDetector class
│   │   ├── object_detector.py  # ObjectDetector (YOLO)
│   │   ├── face_recognizer.py  # FaceRecognizer (dlib)
│   │   ├── ai_thread.py    # AIWorker, draw_detections
│   │   ├── gait_types.py   # GaitBuffer, GaitMatch
│   │   ├── gait_buffer.py  # GaitBufferManager
│   │   ├── gait_engine.py  # GaitEngine (silhouette-based)
│   │   ├── reid_engine.py  # ReIDEngine (body features)
│   │   ├── camera_thread.py # CameraWorker, CameraManager
│   │   └── cleaner.py      # FIFO Storage Manager
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
│   │   ├── camera_dialogs/  # Camera Dialogs (MODULARIZED 2025-12-17)
│   │   │   ├── __init__.py  # Exports LocalCameraSelector, RTSPConfigDialog
│   │   │   ├── local_camera_selector.py # Webcam selection (~230 lines)
│   │   │   └── rtsp_config_dialog.py    # RTSP/IP config (~480 lines)
│   │   ├── face_enrollment/ # Face Enrollment (Modular)
│   │   │   ├── __init__.py
│   │   │   ├── enrollment_dialog.py
│   │   │   ├── manage_dialog.py
│   │   │   └── widgets.py
│   │   ├── settings/        # Settings (Modular)
│   │   │   ├── __init__.py
│   │   │   ├── settings_dialog.py
│   │   │   ├── dialogs/
│   │   │   └── tabs/
│   │   └── dashboard/       # Dashboard Components (Modular)
│   │       ├── __init__.py
│   │       ├── widgets.py   # ActivityItem, ActionCard
│   │       ├── sidebar.py   # SidebarWidget
│   │       ├── home_page.py # HomePage (welcome, cards)
│   │       ├── camera_page.py # CameraPage (video grid)
│   │       └── logs_page.py # LogsPage (filters, export)
│   └── utils/
│       ├── helpers.py      # Image conversion, config, paths
│       ├── logger.py       # Centralized logging
│       ├── i18n.py         # Internationalization (EN, AZ, RU)
│       ├── license_manager.py # Hardware-locked licensing
│       └── auth_manager.py # User authentication
├── tests/
│   └── test_gait_engine.py # Property-based tests (hypothesis)
├── docs/
│   ├── PRD.md              # Product requirements
│   ├── TECH_SPEC.md        # Technical specification
│   ├── LICENSE_SPEC.md     # License system spec
│   ├── database_schema.sql # SQLite schema
│   ├── directory_structure.md # This file
│   └── HANDOVER_OVERVIEW.md # Comprehensive handover documentation (NEW 2025-12-17)
├── memory-bank/            # AI context preservation
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   ├── activeContext.md
│   └── progress.md
├── main.py                 # Application Entry Point
├── build_exe.py            # PyInstaller build script
├── create_setup.py         # Installer creation script
├── admin_keygen.py         # License key generator (ADMIN ONLY)
├── requirements.txt
├── README.md
└── AGENTS.md               # Memory Bank instructions
```

## Module Statistics (2025-12-16)

### src/core/ Line Counts
| File | Lines | Description |
|------|-------|-------------|
| ai_thread.py | 360 | AIWorker, draw_detections |
| gait_engine.py | 327 | GaitEngine core |
| camera_thread.py | 283 | Video capture |
| reid_engine.py | 272 | Re-ID engine |
| cleaner.py | 196 | Storage cleanup |
| face_recognizer.py | 188 | Face recognition |
| object_detector.py | 124 | YOLO wrapper |
| gait_buffer.py | 89 | Buffer management |
| motion_detector.py | 74 | Motion detection |
| detection.py | 34 | Data classes |
| gait_types.py | 21 | Gait data classes |
| __init__.py | 33 | Module exports |

### Refactoring Summary
- **ai_thread.py**: 962 → 360 lines (62% reduction)
- **gait_engine.py**: 652 → 327 lines (50% reduction)
- **camera_dialogs.py**: 843 → 2 files (~710 lines total, 16% reduction)
- **Total modular components**: 10+ files across core/ and ui/
