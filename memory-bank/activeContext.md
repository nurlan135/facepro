# FacePro - Active Context

## Current Work Focus
**Session Date**: 2025-12-15 (Updated: 15:05)

### Completed This Session
1. ✅ Project structure created (all directories)
2. ✅ SQLite database initialized (4 tables)
3. ✅ Core modules implemented:
   - `logger.py` - Centralized logging
   - `helpers.py` - Utility functions
   - `cleaner.py` - FIFO storage manager
   - `camera_thread.py` - Video capture with auto-reconnect
   - `ai_thread.py` - Full AI pipeline
   - `reid_engine.py` - Person Re-ID
   - `gsm_modem.py` - SMS via AT commands
4. ✅ UI components implemented:
   - `styles.py` - Dark theme
   - `video_widget.py` - Video display
   - `settings_dialog.py` - Settings UI
   - `main_window.py` - Main dashboard
5. ✅ License system implemented:
   - `license_manager.py` - Hardware-locked licensing
   - `admin_keygen.py` - Key generator for admin
   - `main.py` - Entry point with license check
6. ✅ **Face Enrollment UI implemented**:
   - `face_enrollment.py` - FaceEnrollmentDialog, ManageFacesDialog
   - Browse image or capture from webcam
   - Face detection validation
   - Database storage with pickle serialization
   - Manage Faces dialog for viewing/deleting
7. ✅ All dependencies installed and working
8. ✅ **License Activation GUI Dialog implemented**:
   - `license_dialog.py` - Modern dark theme UI
   - Machine ID display with copy button
   - License key input with validation
   - Integrated into main.py entry point
9. ✅ **Telegram Notification Integration**:
   - `telegram_notifier.py` - Async bildiriş modulu
   - Rate limiting (spam qoruması)
   - Şəkilli detection alert-ləri
   - Settings-də Test Connection düyməsi
   - Status panel-də Telegram indicator
   - **GSM Fallback Logic**: Offline rejimdə SMS göndərmə (main_window.py) ✅
   - **Event Export**: CSV/JSON ixrac (UTF-8 BOM support) ✅
   - **Re-ID Integration**: AI worker-də Re-ID məntiqi ✅
   - **Multi-language**: AZ, EN, RU dilləri dəstəyi ✅

### Current Machine License
- **Machine ID**: E3B0-C442-98FC-1C14
- **License Key**: 57BKVAPR6MF323U2VSN7
- **Status**: Activated ✅

## Recent Changes
- **License Hardening:** Implemented strict hardware binding (UUID + Volume Serial + CPU ID) to prevent unauthorized copying.
- **Installer Creation:** Created `build_exe.py` and `create_setup.py` to generate a standalone `FacePro_Setup_v1.0.exe` installer.
- **Path Handling Fixes:** Implemented `get_db_path()` and `_ensure_db_initialized()` to handle database creation correctly in "frozen" (exe) mode and fix "no such table" errors.
- **Offline Support:** Ensured `yolov8n.pt` and face recognition models are bundled within the installer.
- **Window Flickering Fix:** Suppressed console window flickering for background processes (ping, wmic) in Windows.

## Active Decisions
- **Database Path:** The database is now located at `data/db/facepro.db` relative to the executable (or `_internal` folder), ensuring portability.
- **Installer Strategy:** Using a custom Python script (`create_setup.py`) wrapping PyInstaller-generated files into a self-extracting executable for simplicity without external dependencies (like Inno Setup).
- **License Key:** License keys are now tied to a robust Machine ID valid only on the specific hardware.

## Current Focus
Transitioning from Development to Deployment/Release phase. The core functionality and packaging are complete.

## Next Steps
1.  **User Documentation:** Create a user manual (PDF/HTML) to include with the installer.
2.  **Refurbished Mini PC Bundle:** (Business Task) Prepare the "FacePro AI Box" strategy.
3.  **Final Testing:** Full end-to-end test on a fresh machine (Virtual Machine) to verify the installer.
 ✅

### Medium-term
9. [x] Re-ID integration into pipeline ✅
10. [ ] Performance optimization
11. [x] Multi-language support (AZ, EN, RU) ✅
13. [ ] License Hardening (Hardware-locked + Machine ID binding)
## Active Decisions

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
- `users` table: id, name, created_at (NO role column)
- `face_encodings` table: id, user_id, encoding (NO image_path column)
- `reid_embeddings` table: for future Re-ID vectors
- `events` table: detection history

### UI Guidelines
- Dark theme only (for now)
- Consistent color coding (green=known, red=unknown)
- Status indicators for connection states

## Learnings and Project Insights

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

### Face Recognition Flow
1. Enroll: Image → face_recognition.face_encodings() → pickle → BLOB
2. Load: BLOB → pickle.loads() → numpy array
3. Match: face_recognition.face_distance() → threshold check
