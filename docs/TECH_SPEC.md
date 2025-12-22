# Technical Specification (FacePro v1.0)

## 1. System Architecture
The application follows a modular **Model-View-Controller (MVC)** pattern adapted for a Desktop GUI application.

### 1.1. Concurrency Model (Threading & Services)
To prevent the GUI from freezing, the application MUST use `QThread` for all heavy operations:
* **Main Thread (UI):** Handles PyQt6 event loop, button clicks, and image rendering.
* **Camera Thread (`CameraWorker`):**
    * Connects to RTSP/Webcam using `cv2.VideoCapture`.
    * Maintains a specific FPS (e.g., 30 FPS) reading rate.
    * Handles **Auto-Reconnect** logic.
    * Emits `raw_frame_signal` to the AI Thread.
* **AI Thread (`AIWorker`) - The Orchestrator:**
    *   **Role:** Coordinates the pipeline by calling specialized services.
    *   **DetectionService:** Motion Detection and YOLO.
    *   **RecognitionService:** Face, Re-ID, and Gait logic.
    *   **MatchingService:** In-Memory Vector Operations.
    *   Emits `processed_frame_signal` back to Main Thread.
* **Storage Thread (`StorageWorker`) - Async I/O:**
    *   Handles all Disk I/O (Snapshots) and DB Inserts (Events & Embeddings).
    *   Receives tasks via `Queue` to ensure non-blocking AI pipeline.

### 1.2. Internationalization (i18n)
* **Format:** JSON files in `locales/` (`en.json`, `az.json`, `ru.json`).
* **Mechanism:**
    *   `Translator` singleton loads JSON on startup.
    *   UI components subscribe to `language_changed` signal.
    *   Dynamic text updates without app restart (mostly).
*   **Validation:** Pydantic models validate JSON structure.

## 2. The AI Pipeline Logic (Service-Driven)
The AI processing follows this sequential logic, delegated to services:

1.  **Motion Detection (Gatekeeper) [DetectionService]:**
    * Convert frame to Grayscale -> Gaussian Blur.
    * Calculate `cv2.absdiff` with background.
    * **IF** motion pixels < Threshold: Skip AI, return frame immediately.
    * **ELSE**: Proceed to Object Detection.

2.  **Object Detection (YOLOv8n) [DetectionService]:**
    * Model: `yolov8n.pt`.
    * Classes: Filter only `Person (0)`, `Cat (15)`, `Dog (16)`.
    * **IF** Person detected: Crop the person's image -> Proceed to Recognition.

3.  **Identity Resolution [RecognitionService]:**
    * **Step A: Face Quality Check [FaceQualityService]:**
        * Validate Image Size (> 64x64px).
        * Blur Detection (Laplacian Variance, Threshold: 100).
        * Brightness Check (Not too dark/bright).
    * **Step B: Face Recognition (InsightFace):**
        * Backend: `ArcFace (ResNet100)` -> 512d Embedding.
        * Compare with 512d vectors in `EmbeddingRepository`.
        * Threshold: > 0.6 (Confidence).
        * If Match Found (e.g., "Ali"):
            * **Passive Enrollment:** Extract the *Body Embedding* and update profile via `StorageWorker`.
    * **Step C: Body Re-ID & Gait [MatchingService]:**
        * If face is NOT visible, extract Body/Gait Embedding.
        * Compare with stored vectors in `MatchingService` (Cosine Similarity).
        * Threshold: > 0.75 (Confidence).
        * If Match: Label as "Ali (Re-ID)" or "Ali (Gait)".

## 3. Hardware & Storage Specs

### 3.1. Storage (FIFO Policy)
* **Root Path:** `./data/recordings/`
* **Logic:** A background timer (every 10 mins) checks folder size.
* **Action:** If size > `MAX_SIZE` (e.g., 5GB), delete the oldest files based on creation time (`os.path.getctime`) until size is within limits.

### 3.2. GSM Module Integration (Offline Mode)
* **Library:** `pyserial`
* **Trigger:** When `InternetCheck()` fails AND `PersonDetected()` is True.
* **Protocol:** AT Commands.
    * `AT` (Check connection)
    * `AT+CMGF=1` (Set Text Mode)
    * `AT+CMGS="+99450xxxxxxx"` (Send SMS)

### 3.3. Backup & Restore
* **Format:** ZIP Archive containing:
    *   `facepro.db` (SQLite Database)
    *   `config/*.json` (Settings)
    *   `data/faces/` (Face Images)
    *   `backup_meta.json` (Version info)
*   **Process:** Background thread (`BackupWorker`) prevents GUI freeze.
*   **Restore:** Validates structure before overwriting current data.

## 4. Error Handling
* **RTSP Failures:** Do not crash. Log error, show "Reconnecting..." overlay on UI, and retry indefinitely.
* **Model Loading:** If GPU is missing, silently fallback to CPU mode.

## 5. User Authentication System

### 5.1. Authentication Flow
1. **First Launch:** If no users exist in `app_users` table, show SetupWizard to create first admin account.
2. **Normal Launch:** Show LoginDialog before main dashboard.
3. **Session Management:** Track login time, auto-logout after configurable timeout (default 30 min).

### 5.2. Password Security
* **Hashing:** `bcrypt` (Legacy SHA-256 supported for smooth migration)
* **Storage:** `password_hash` (salt embedded in hash for bcrypt)
* **Verification:** `bcrypt.checkpw(password, hash)`

### 5.3. Account Lockout
* **Trigger:** 3 consecutive failed login attempts
* **Duration:** 5 minutes
* **Reset:** Automatic after lockout period expires

### 5.4. Role-Based Access Control (RBAC)
| Feature | Admin | Operator |
|---------|-------|----------|
| Camera Monitoring | ✅ | ✅ |
| Event Logs | ✅ | ✅ |
| Change Own Password | ✅ | ✅ |
| Settings | ✅ | ❌ |
| User Management | ✅ | ❌ |
| Face Enrollment | ✅ | ❌ |

### 5.5. Session Timeout
* **Default:** 30 minutes of inactivity
* **Configurable:** 5-120 minutes (Admin only)
* **Action:** Auto-logout, stop camera streams, return to login screen

### 5.6. Audit Trail
*   **Purpose:** Track administrative actions for security and accountability.
*   **Events Logged:**
    *   Authentication: `LOGIN`, `LOGOUT`, `LOGIN_FAILED`.
    *   User Management: `USER_CREATED`, `USER_DELETED`, `PASSWORD_CHANGED`.
    *   Enrollment: `FACE_ENROLLED`, `FACE_DELETED`, `PERSON_DELETED`.
    *   System: `SETTINGS_CHANGE`, `BACKUP_CREATED`, `DATABASE_RESTORED`.
*   **Storage:** `audit_logs` table.
*   **Access:** Visible only to Admins via "Audit Logs" tab.

## 6. Database & Migrations
*   **Engine:** SQLite (`data/db/facepro.db`).
*   **Migration System:**
    *   Migrations stored in `migrations/` folder (e.g., `004_add_audit_logs.sql`).
    *   `schema_migrations` table tracks applied versions.
    *   Automated migration on app startup via `MigrationRunner`.
*   **Key Tables:**
    *   `users`: Registered identities.
    *   `face_encodings`: 512d InsightFace vectors.
    *   `events`: Detection history (snapshot paths).
    *   `audit_logs`: Administrative action history.
    *   `app_users`: Login credentials (bcrypt hashed).