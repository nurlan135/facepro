-- SQLite Schema for FacePro

-- 1. Users (People allowed/registered)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Face Encodings (Standard Face Rec)
CREATE TABLE IF NOT EXISTS face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    encoding BLOB NOT NULL, -- Serialized numpy array (128d)
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

-- 4. Event Logs (History displayed in UI)
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,       -- 'PERSON', 'INTRUSION', 'OFFLINE_ALERT'
    object_label TEXT,     -- 'Ali', 'Unknown', 'Cat'
    confidence REAL,
    snapshot_path TEXT,    -- Path to .jpg in /data/logs/
    is_sent_telegram BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);