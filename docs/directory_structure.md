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
│   ├── yolov8n.pt          # Object Detection weights
│   ├── dlib_face_recognition_resnet_model_v1.dat
│   └── efficientnet_b0.pth # Re-ID Feature Extractor
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── camera_thread.py # QThread for Video Capture & Reconnect
│   │   ├── ai_thread.py     # QThread for Pipeline (Motion->YOLO->ReID)
│   │   ├── reid_engine.py   # Specific logic for Body Feature Extraction
│   │   └── cleaner.py       # FIFO Storage Manager
│   ├── hardware/
│   │   ├── __init__.py
│   │   └── gsm_modem.py     # Serial AT Commands wrapper
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py   # Main Dashboard (Grid View)
│   │   ├── video_widget.py  # Custom PyQt Label for Video
│   │   ├── settings_dialog.py
│   │   └── styles.py
│   └── utils/
│   │   ├── helpers.py       # Image conversion (CV2 -> QPixmap)
│   │   └── logger.py
├── main.py                 # Application Entry Point
├── requirements.txt
└── README.md