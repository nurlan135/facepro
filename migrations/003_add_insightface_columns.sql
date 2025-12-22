-- migrations/003_add_insightface_columns.sql

-- Add embedding dimension tracking to face_encodings
-- SQLite doesn't support IF NOT EXISTS for ADD COLUMN, so we'll wrap this in try-except in runner or handle it here if possible.
-- For standard SQL execution scripts, we just provide the command.

ALTER TABLE face_encodings ADD COLUMN embedding_dim INTEGER DEFAULT 128;
ALTER TABLE face_encodings ADD COLUMN backend TEXT DEFAULT 'dlib';

-- Update schema version
INSERT INTO schema_migrations (version, name) VALUES (3, '003_add_insightface_columns');
