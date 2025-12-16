# Project Directory Structure

FacePro/
├── assets/                 # Icons (.ico), logo.png, UI styles (.qss)
├── config/
│   ├── settings.json       # App config (Telegram token, threshold, paths)
│   └── cameras.json        # Saved camera list (RTSP URLs)
├── data/
│   ├── db/
│   │   └── faceguard.db    # SQLite Database (Metadata)
│   ├── faces/              # Registered user reference images (jpg)
│   └── logs/               # Event snapshots (saved detections)
├── models/
│   ├── yolov8n.pt          # Object Detection weights (YOLOv8 nano)
│   └── efficientnet_b0.pth # Re-ID Feature Extractor (optional, uses pretrained if missing)
│   # Note: dlib face model is auto-downloaded by face_recognition library
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── camera_thread.py # QThread for Video Capture & Reconnect
│   │   ├── ai_thread.py     # QThread for Pipeline (Motion->YOLO->ReID)
│   │   ├── reid_engine.py   # Specific logic for Body Feature Extraction
│   │   └── cleaner.py       # FIFO Storage Manager
│   ├── hardware/
│   │   ├── __init__.py
│   │   ├── gsm_modem.py     # Serial AT Commands wrapper
│   │   └── telegram_notifier.py # Telegram Bot Integration
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main Dashboard (Coordinator)
│   │   ├── video_widget.py  # Custom PyQt Label for Video
│   │   ├── settings_dialog.py
│   │   ├── face_enrollment.py # Face registration dialogs
│   │   ├── license_dialog.py  # License activation
│   │   ├── zone_editor.py     # ROI zone editor
│   │   ├── styles.py
│   │   └── dashboard/         # Dashboard Components (Modular)
│   │       ├── __init__.py
│   │       ├── widgets.py     # ActivityItem, ActionCard
│   │       ├── sidebar.py     # SidebarWidget
│   │       ├── home_page.py   # HomePage (welcome, cards)
│   │       ├── camera_page.py # CameraPage (video grid)
│   │       └── logs_page.py   # LogsPage (filters, export)
│   └── utils/
│       ├── helpers.py       # Image conversion (CV2 -> QPixmap)
│       ├── logger.py
│       ├── i18n.py          # Internationalization (EN, AZ, RU)
│       └── license_manager.py # Hardware-locked licensing
├── main.py                 # Application Entry Point
├── build_exe.py            # PyInstaller build script
├── create_setup.py         # Installer creation script
├── requirements.txt
└── README.md