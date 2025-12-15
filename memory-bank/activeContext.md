# FacePro - Active Context

## Current Work Focus
**Session Date**: 2025-12-15 (Updated: 20:30)

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
   - `main_window.py` - Main dashboard (refactored)
5. ✅ License system implemented
6. ✅ **Face Enrollment UI implemented**
7. ✅ **License Activation GUI Dialog implemented**
8. ✅ **Telegram Notification Integration**
9. ✅ **Dashboard UI Redesign** (FaceGuard Pro theme)
10. ✅ **UI Modularization** - main_window.py refactored:
    - `src/ui/dashboard/widgets.py` - ActivityItem, ActionCard
    - `src/ui/dashboard/sidebar.py` - SidebarWidget
    - `src/ui/dashboard/home_page.py` - HomePage
    - `src/ui/dashboard/camera_page.py` - CameraPage
    - `src/ui/dashboard/logs_page.py` - LogsPage with filters
11. ✅ **Live Language Switching** - UI updates without restart
12. ✅ **Enhanced Logs Page**:
    - Filter buttons (All/Known/Unknown)
    - Entry count display
    - Duplicate prevention (2 sec cooldown)
    - Camera name in entries
    - Date + Time format

### Current Machine License
- **Machine ID**: E3B0-C442-98FC-1C14
- **License Key**: 57BKVAPR6MF323U2VSN7
- **Status**: Activated ✅

## Recent Changes
- **UI Modularization:** Split main_window.py (730→350 lines) into dashboard components.
- **Live Language Switching:** Using QObject signals for real-time translation updates.
- **Logs Filtering:** Added All/Known/Unknown filters with entry count.
- **Duplicate Prevention:** Same person detection throttled to 2 seconds.
- **Camera Name Display:** Each log entry shows which camera detected it.

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
