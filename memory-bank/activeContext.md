# FacePro - Active Context

## Current Work Focus
**Session Date**: 2025-12-16 (Updated)

### Completed This Session (2025-12-16)
1. ✅ **User Login System Implementation** (Task 10):
   - `SetupWizardDialog` - İlk admin hesabı yaratma
   - `LoginDialog` - İstifadəçi girişi
   - `UserManagementDialog` - İstifadəçi idarəetməsi (Admin only)
   - `ChangePasswordDialog` - Şifrə dəyişmə
   - `AuthManager` - Autentifikasiya və sessiya idarəetməsi

2. ✅ **i18n (Internationalization) Updates**:
   - Bütün Login/Auth UI komponentləri üçün tərcümələr (EN, AZ, RU)
   - Setup Wizard, Login Dialog, User Management, Change Password
   - Sidebar düymələri (Logout, User Management, Change Password)
   - Session timeout mesajları
   - Error mesajları

3. ✅ **Role-Based Access Control**:
   - Admin: Tam səlahiyyət (ayarlar, istifadəçi idarəetməsi, üz qeydiyyatı)
   - Operator: Məhdud səlahiyyət (yalnız monitorinq və jurnallar)
   - Sidebar düymələri rol əsasında gizlədilir

4. ✅ **Security Improvements**:
   - Proqramdan çıxanda avtomatik logout
   - Session timeout (30 dəqiqə default)
   - Account lockout (3 uğursuz cəhddən sonra 5 dəqiqə)
   - SHA-256 + salt ilə şifrə hash-ləmə

### Previous Session Completions
- Project structure, SQLite database, Core modules
- UI components, License system, Face Enrollment
- Dashboard UI Redesign, UI Modularization
- Live Language Switching, Enhanced Logs Page
- Telegram Notification Integration

### Current Machine License
- **Machine ID**: E3B0-C442-98FC-1C14
- **License Key**: 57BKVAPR6MF323U2VSN7
- **Status**: Activated ✅

## Recent Changes
- **User Authentication:** Full login system with setup wizard for first-time use
- **Role-Based UI:** Operator users see limited sidebar options
- **i18n Complete:** All auth-related UI translated to AZ, EN, RU
- **Exit/Logout Distinction:** "Hesabdan Çıx" vs "Proqramdan Çıx" ayrılıb

## Active Decisions
- **Database Path:** `data/db/facepro.db` (app_users table added for auth)
- **Password Storage:** SHA-256 hash with unique salt per user
- **Session Management:** 30 minute timeout, configurable 5-120 minutes
- **Role System:** Admin (full access) vs Operator (monitoring only)

## Current Focus
User Login System implementation complete. Ready for final testing and deployment.

## Next Steps
1. **Final Testing:** Test all auth flows (setup, login, logout, password change)
2. **User Documentation:** Update user manual with login instructions
3. **Deployment:** Package and distribute
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
