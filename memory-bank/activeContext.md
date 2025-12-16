# FacePro - Active Context

## Current Work Focus
**Session Date**: 2025-12-16 (Updated)

### Completed This Session (2025-12-16)
1. ✅ **Gait Recognition System Implementation** (TAMAMLANDI):
   - `GaitEngine` - Yeriş tanıma mühərriki (src/core/gait_engine.py)
   - `GaitBufferManager` - Track ID üçün silhouette buffer idarəsi
   - Silhouette extraction (64x64 binary images)
   - 256D embedding extraction (ResNet18-based)
   - Cosine similarity matching
   - Database operations (save/load embeddings)
   - Passive enrollment (üz tanındıqda avtomatik gait öyrənmə)
   - AIWorker integration (_try_gait_recognition, gait fallback)
   - Settings integration (gait_enabled, gait_threshold, gait_sequence_length)
   - i18n translations (EN, AZ, RU)
   - Property-based tests (hypothesis ilə 10+ test)

2. ✅ **User Login System** (Əvvəlki sessiya):
   - SetupWizardDialog, LoginDialog, UserManagementDialog
   - AuthManager, Role-Based Access Control
   - Session timeout, Account lockout

### Previous Session Completions
- Project structure, SQLite database, Core modules
- UI components, License system, Face Enrollment
- Dashboard UI Redesign, UI Modularization
- Live Language Switching, Enhanced Logs Page
- Telegram Notification Integration
- User Authentication System

### Current Machine License
- **Machine ID**: E3B0-C442-98FC-1C14
- **License Key**: 57BKVAPR6MF323U2VSN7
- **Status**: Activated ✅

## Recent Changes
- **Gait Recognition:** Full gait recognition pipeline implemented
- **Database:** gait_embeddings table added
- **AIWorker:** Gait fallback after Re-ID fails
- **Settings:** Gait configuration options added
- **Events:** identification_method column added ('face', 'reid', 'gait', 'unknown')

## Active Decisions
- **Gait Sequence Length:** 30 frames (configurable 20-60)
- **Gait Threshold:** 0.70 default (configurable 0.5-0.95)
- **Silhouette Size:** 64x64 pixels (fixed)
- **Embedding Dimension:** 256D (ResNet18 feature extractor)
- **Max Embeddings Per User:** 10 (FIFO - oldest deleted)
- **Buffer Timeout:** 5 seconds (stale buffers removed)

## Current Focus
Code modularization complete. ai_thread.py and gait_engine.py refactored.

## Next Steps
1. **Real-world Testing:** Test gait recognition with actual walking videos
2. **Performance Optimization:** GPU acceleration for gait model
3. **User Documentation:** Update manual with gait recognition info
4. **RTSP Camera Testing:** Validate with real CCTV streams

## Recent Refactoring (2025-12-16)
### ai_thread.py Modularization
- **Before:** 962 sətir, 1 fayl
- **After:** 5 fayla bölündü
  - `detection.py` (34 sətir) - DetectionType, Detection, FrameResult
  - `motion_detector.py` (74 sətir) - MotionDetector class
  - `object_detector.py` (124 sətir) - ObjectDetector (YOLO)
  - `face_recognizer.py` (188 sətir) - FaceRecognizer (dlib)
  - `ai_thread.py` (360 sətir) - AIWorker, draw_detections

### gait_engine.py Modularization
- **Before:** 652 sətir, 1 fayl
- **After:** 3 fayla bölündü
  - `gait_types.py` (21 sətir) - GaitBuffer, GaitMatch dataclasses
  - `gait_buffer.py` (89 sətir) - GaitBufferManager class
  - `gait_engine.py` (327 sətir) - GaitEngine core
## Active Decisions

### User Authentication System
- **Password Hashing:** SHA-256 with unique salt per user
- **Session Timeout:** 30 minutes default, configurable 5-120 min
- **Account Lockout:** 3 failed attempts = 5 minute lock
- **Role System:** Admin (full) vs Operator (limited)
- **Database Table:** `app_users` (id, username, password_hash, salt, role, created_at, failed_attempts, locked_until)

### License System
- Using SHA-256 + Base32 encoding
- Salt is hardcoded (should be obfuscated in production)
- Machine ID = hash of CPU + Motherboard IDs
- `.license` file stored in app root

### Face Enrollment
- Images stored in `data/faces/` folder
- Encodings serialized with pickle, stored as BLOB
- One user can have multiple face encodings
- Face detection required before save

### AI Pipeline
- Motion detection as gatekeeper (saves CPU)
- YOLO for object detection (person/cat/dog only)
- face_recognition for known face matching
- Faces loaded from database on AIWorker start

### Threading Model
- Main thread for UI
- Separate thread per camera
- Single AI thread (processes frames from all cameras)
- Background cleanup thread (10 min interval)

## Important Patterns and Preferences

### Code Style
- Azeri comments preferred where appropriate
- English for API/function names
- Type hints used throughout
- Docstrings for all public functions

### Error Handling
- Graceful degradation (skip if component fails)
- Log all errors with full context
- Never crash the UI thread

### Database Schema
- `users` table: id, name, created_at (face recognition users)
- `app_users` table: id, username, password_hash, salt, role, etc. (login system)
- `face_encodings` table: id, user_id, encoding
- `reid_embeddings` table: for future Re-ID vectors
- `events` table: detection history

### UI Guidelines
- Dark theme only (for now)
- Consistent color coding (green=known, red=unknown)
- Status indicators for connection states
- Role-based UI visibility (hide admin features for operators)

### i18n (Internationalization)
- Three languages: English (en), Azerbaijani (az), Russian (ru)
- Translation function: `tr("key")` from `src/utils/i18n.py`
- Live language switching without restart
- All UI text should use translation keys

## Learnings and Project Insights

### User Authentication
- Setup wizard appears only when no users exist in database
- Login dialog blocks main window until successful auth
- Logout clears session and returns to login
- Exit from app also logs out for security

### Role-Based Access
- Admin: Settings, User Management, Face Enrollment visible
- Operator: Only monitoring, logs, and password change visible
- Implemented in `sidebar.set_user_info()` method

### dlib Installation
- Requires Visual Studio Build Tools + CMake
- Takes ~10 minutes to compile on first install
- Pre-built wheels not available for Python 3.12

### Python 3.14 Compatibility
- NOT recommended - many packages lack wheels
- Python 3.12 is the safe choice

### Database Schema Sync
- Always check actual schema before writing SQL
- Don't assume columns exist (role, image_path were not in schema)
