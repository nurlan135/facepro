-- Migration: PROD-013 Audit Trail System
-- Description: Adds a table to track administrative and security actions.

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type TEXT NOT NULL,  -- 'LOGIN', 'LOGOUT', 'SETTINGS_CHANGE', 'FACE_ENROLLED', 'USER_DELETED', 'BACKUP_CREATED', 'DATABASE_RESTORED'
    details TEXT,               -- JSON data for context (e.g., {"tab": "AI", "field": "motion_threshold"})
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES app_users(id)
);

-- Index for faster filtering by action or user
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at);
