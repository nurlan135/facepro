# Sprint 5: Təhlükəsizlik Auditi və UX Təkmilləşdirilməsi
> **Müddət:** 2 həftə  
> **Başlanğıc:** Sprint 4 bitdikdən sonra  
> **Hədəf:** Audit trail sistemi, Enrollment keyfiyyət yoxlanışı və Sistem optimallaşdırması

---

## 📋 Task Board

### 🔲 To Do

#### PROD-013: Audit Trail / Activity Logs (4 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 5.1.1 | `audit_logs` cədvəli yaradılması (Migration) | | 0.5d | ✅ |
| 5.1.2 | `AuditLogger` utilit sinfi | | 0.5d | ✅ |
| 5.1.3 | Login/Logout hadisələrinin loglanması | | 0.5d | ✅ |
| 5.1.4 | Ayarlar dəyişikliklərinin loglanması | | 1d | ✅ |
| 5.1.5 | Qeydiyyat (Face Enrollment) loglanması | | 0.5d | ✅ |
| 5.1.6 | Audit Logs UI Tab (Admin only) | | 1d | ✅ |

---

#### PROD-014: Face Enrollment UX Improvement (3 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 5.2.1 | Blur detection (Laplacian variance) | | 0.5d | ✅ |
| 5.2.2 | Face quality score (InsightFace) | | 1d | ✅ |
| 5.2.3 | Multi-face detection prevention | | 0.5d | ✅ |
| 5.2.4 | Enrollment dialog UI feedback (Real-time quality) | | 1d | ✅ |

---

#### PROD-015: Sistem Optimallaşdırması (3 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 5.3.1 | RAM usage optimization (Embedding cache) | | 1d | ✅ |
| 5.3.2 | Lazy loading for historical logs | | 1d | ✅ |
| 5.3.3 | Startup speed optimization | | 1d | ✅ |

---

## 🗒️ Detallar

### 5.1.1 Audit Logs Migration
```sql
-- migrations/004_add_audit_logs.sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type TEXT NOT NULL,  -- 'LOGIN', 'LOGOUT', 'SETTINGS_CHANGE', 'FACE_ENROLLED', 'USER_DELETED'
    details TEXT,               -- JSON data for more context
    ip_address TEXT,            -- optional
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES app_users(id)
);

INSERT INTO schema_migrations (version, name) VALUES (4, '004_add_audit_logs');
```

### 5.1.2 AuditLogger Implementation
```python
# src/utils/audit_logger.py
import json
from src.core.database.db_manager import DatabaseManager

class AuditLogger:
    @staticmethod
    def log(action_type: str, details: dict = None, user_id: int = None):
        db = DatabaseManager()
        query = "INSERT INTO audit_logs (user_id, action_type, details) VALUES (?, ?, ?)"
        db.execute_write(query, (user_id, action_type, json.dumps(details) if details else None))
```

---

## 🧪 Test Planı

- `test_audit_logger.py`: Logların bazaya düzgün yazılmasını yoxla.
- `test_enrollment_quality.py`: Bulanlıq şəkillərin rədd edilməsini yoxla.
