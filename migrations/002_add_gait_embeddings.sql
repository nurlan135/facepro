-- migrations/002_add_gait_embeddings.sql

-- Gait recognition embeddings table
CREATE TABLE IF NOT EXISTS gait_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    confidence REAL DEFAULT 1.0,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Re-ID embeddings table
CREATE TABLE IF NOT EXISTS reid_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vector BLOB NOT NULL,
    confidence REAL DEFAULT 1.0,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for faster gait lookups
CREATE INDEX IF NOT EXISTS idx_gait_user ON gait_embeddings(user_id);

-- Update schema version
INSERT INTO schema_migrations (version, name) VALUES (2, '002_add_gait_embeddings');
