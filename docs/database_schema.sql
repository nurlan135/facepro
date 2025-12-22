-- SQLite Schema for FacePro (Updated 2025-12-22)

-- 0. Schema Migrations (Tracks database version)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1. Users (People allowed/registered)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Face Encodings (InsightFace / dlib)
CREATE TABLE IF NOT EXISTS face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    encoding BLOB NOT NULL, -- Serialized numpy array (128d for dlib, 512d for InsightFace)
    embedding_dim INTEGER DEFAULT 128, -- 128 or 512
    backend TEXT DEFAULT 'dlib',       -- 'dlib' or 'insightface'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. Re-ID Embeddings (Body/Clothing Vectors)
-- This table is dynamic. New vectors are added when Face Rec confirms identity.
CREATE TABLE IF NOT EXISTS reid_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    vector BLOB NOT NULL,   -- Serialized numpy array (EfficientNet Output)
    confidence REAL,        -- How sure we were when adding this
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Gait Embeddings (Walking Pattern Vectors)
CREATE TABLE IF NOT EXISTS gait_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,   -- Serialized numpy array (256d GaitSet output)
    confidence REAL DEFAULT 1.0,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_gait_user ON gait_embeddings(user_id);

-- 5. Event Logs (History displayed in UI)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,       -- 'PERSON', 'INTRUSION', 'OFFLINE_ALERT'
    object_label TEXT,     -- 'Ali', 'Unknown', 'Cat'
    confidence REAL,
    snapshot_path TEXT,    -- Path to .jpg in /data/logs/
    identification_method TEXT DEFAULT 'unknown',  -- 'face', 'reid', 'gait', 'unknown'
    is_sent_telegram BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Application Users (Login System)
CREATE TABLE IF NOT EXISTS app_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,  -- bcrypt hash (starts with $2b$)
    salt TEXT NOT NULL,           -- Embedded in hash for bcrypt (kept for legacy SHA256 support)
    role TEXT NOT NULL DEFAULT 'operator',  -- 'admin' or 'operator'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,  -- For account lockout
    locked_until TIMESTAMP              -- Lock expiry time
);

-- 7. Audit Logs (Administrative Actions)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type TEXT NOT NULL,  -- 'LOGIN', 'SETTINGS_CHANGE', 'FACE_ENROLLED', etc.
    details TEXT,               -- JSON data for more context
    ip_address TEXT,            -- optional
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES app_users(id)
);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);