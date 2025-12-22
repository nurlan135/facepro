# Sprint 4: Database, Backup və Performance
> **Müddət:** 2 həftə  
> **Başlanğıc:** Sprint 3 bitdikdən sonra  
> **Hədəf:** Database migration sistemi, export/backup, performance monitoring

---

## 📋 Task Board

### 🔲 To Do

#### PROD-010: Database Migration System (4 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 4.1.1 | `migrations/` qovluğu yaratmaq | | 0.5d | ✅ |
| 4.1.2 | Schema versioning table | | 0.5d | ✅ |
| 4.1.3 | Migration runner utility | | 1.5d | ✅ |
| 4.1.4 | Rollback support | | 1d | ✅ |
| 4.1.5 | Auto-migration on startup | | 0.5d | ✅ |

**Detallar:**

##### 4.1.1 Migration Qovluq Strukturu
```
migrations/
├── 001_initial_schema.sql
├── 002_add_gait_embeddings.sql
├── 003_add_insightface_columns.sql
├── 004_add_notification_settings.sql
└── runner.py
```

##### 4.1.2 Schema Versioning Table
```sql
-- migrations/001_initial_schema.sql

-- Schema version tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT
);

-- Insert initial version
INSERT INTO schema_migrations (version, name) VALUES (1, '001_initial_schema');

-- Original tables (if not exists from db_manager)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    encoding BLOB NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    object_label TEXT,
    confidence REAL,
    snapshot_path TEXT,
    identification_method TEXT DEFAULT 'unknown',
    camera_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

```sql
-- migrations/002_add_gait_embeddings.sql

-- Gait recognition embeddings table
CREATE TABLE IF NOT EXISTS gait_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Re-ID embeddings table
CREATE TABLE IF NOT EXISTS reid_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Update schema version
INSERT INTO schema_migrations (version, name) VALUES (2, '002_add_gait_embeddings');
```

```sql
-- migrations/003_add_insightface_columns.sql

-- Add embedding dimension tracking
ALTER TABLE face_encodings ADD COLUMN embedding_dim INTEGER DEFAULT 128;
ALTER TABLE face_encodings ADD COLUMN backend TEXT DEFAULT 'dlib';

-- Update schema version
INSERT INTO schema_migrations (version, name) VALUES (3, '003_add_insightface_columns');
```

##### 4.1.3 Migration Runner
```python
# migrations/runner.py

import os
import re
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

from src.utils.logger import get_logger
from src.utils.helpers import get_db_path

logger = get_logger()

class MigrationRunner:
    """Database migration runner with versioning and rollback support"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self.migrations_dir = Path(__file__).parent
    
    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def get_current_version(self) -> int:
        """Get current schema version from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT MAX(version) FROM schema_migrations")
            result = cursor.fetchone()
            return result[0] if result[0] else 0
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return 0
        finally:
            conn.close()
    
    def get_available_migrations(self) -> List[Tuple[int, str, Path]]:
        """Get list of available migration files"""
        migrations = []
        
        for file in sorted(self.migrations_dir.glob("*.sql")):
            match = re.match(r"(\d+)_(.+)\.sql", file.name)
            if match:
                version = int(match.group(1))
                name = match.group(2)
                migrations.append((version, name, file))
        
        return migrations
    
    def get_pending_migrations(self) -> List[Tuple[int, str, Path]]:
        """Get migrations that haven't been applied yet"""
        current_version = self.get_current_version()
        all_migrations = self.get_available_migrations()
        
        return [(v, n, p) for v, n, p in all_migrations if v > current_version]
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of migration file"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def apply_migration(self, version: int, name: str, file_path: Path) -> bool:
        """Apply a single migration"""
        logger.info(f"Applying migration {version}: {name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Execute migration
            cursor.executescript(sql)
            
            # Record migration (if not already in script)
            checksum = self.calculate_checksum(file_path)
            cursor.execute("""
                INSERT OR IGNORE INTO schema_migrations (version, name, checksum)
                VALUES (?, ?, ?)
            """, (version, f"{version:03d}_{name}", checksum))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Migration {version} applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            return False
    
    def migrate(self, target_version: Optional[int] = None) -> bool:
        """Run all pending migrations up to target version"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("Database is up to date")
            return True
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        for version, name, file_path in pending:
            if target_version and version > target_version:
                break
            
            if not self.apply_migration(version, name, file_path):
                return False
        
        return True
    
    def rollback(self, target_version: int) -> bool:
        """
        Rollback to a specific version.
        Note: Requires corresponding rollback SQL files.
        """
        current = self.get_current_version()
        
        if target_version >= current:
            logger.warning("Target version is not lower than current")
            return False
        
        # Look for rollback files
        for version in range(current, target_version, -1):
            rollback_file = self.migrations_dir / f"{version:03d}_rollback.sql"
            
            if not rollback_file.exists():
                logger.error(f"Rollback file not found: {rollback_file}")
                return False
            
            logger.info(f"Rolling back migration {version}")
            
            try:
                with open(rollback_file, 'r', encoding='utf-8') as f:
                    sql = f.read()
                
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.executescript(sql)
                
                # Remove migration record
                cursor.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"Rollback {version} failed: {e}")
                return False
        
        return True
    
    def status(self):
        """Print migration status"""
        current = self.get_current_version()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        print(f"Current schema version: {current}")
        print(f"Available migrations: {len(available)}")
        print(f"Pending migrations: {len(pending)}")
        
        if pending:
            print("\nPending:")
            for v, n, _ in pending:
                print(f"  - {v:03d}_{n}")


# Standalone execution
if __name__ == '__main__':
    import sys
    
    runner = MigrationRunner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'status':
            runner.status()
        elif command == 'migrate':
            target = int(sys.argv[2]) if len(sys.argv) > 2 else None
            runner.migrate(target)
        elif command == 'rollback':
            target = int(sys.argv[2])
            runner.rollback(target)
        else:
            print(f"Unknown command: {command}")
    else:
        runner.status()
```

##### 4.1.5 Auto-migration on Startup
```python
# Fayl: src/core/database/db_manager.py (əlavə)

from migrations.runner import MigrationRunner

class DatabaseManager:
    def __init__(self):
        # ... existing ...
        self._run_migrations()
    
    def _run_migrations(self):
        """Auto-run pending migrations on startup"""
        try:
            runner = MigrationRunner(self.db_path)
            pending = runner.get_pending_migrations()
            
            if pending:
                logger.info(f"Running {len(pending)} pending database migrations...")
                if runner.migrate():
                    logger.info("Database migrations completed successfully")
                else:
                    logger.error("Database migration failed!")
        except Exception as e:
            logger.error(f"Migration check failed: {e}")
```

---

#### PROD-011: Export/Backup Funksionallığı (3 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 4.2.1 | Database backup utility | | 0.5d | ✅ |
| 4.2.2 | Faces export (ZIP) | | 0.5d | ✅ |
| 4.2.3 | Settings export (JSON) | | 0.5d | ✅ |
| 4.2.4 | Full backup wizard UI | | 1d | ✅ |
| 4.2.5 | Restore functionality | | 0.5d | ✅ |

**Detallar:**

##### 4.2.1-3 Backup Utility
```python
# Yeni fayl: src/utils/backup_manager.py

import os
import shutil
import zipfile
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import sqlite3

from src.utils.logger import get_logger
from src.utils.helpers import get_db_path, load_config

logger = get_logger()

class BackupManager:
    """Handles backup and restore operations"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        base_dir = Path(__file__).parent.parent.parent
        self.backup_dir = Path(backup_dir) if backup_dir else base_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        self.db_path = get_db_path()
        self.faces_dir = base_dir / 'data' / 'faces'
        self.config_path = base_dir / 'config' / 'settings.json'
    
    def create_backup(self, 
                      include_db: bool = True,
                      include_faces: bool = True,
                      include_settings: bool = True) -> Tuple[bool, str]:
        """
        Create a full or partial backup.
        
        Returns:
            (success, path_or_error_message)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"facepro_backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Backup manifest
                manifest = {
                    'version': '1.0',
                    'created_at': datetime.now().isoformat(),
                    'includes': {
                        'database': include_db,
                        'faces': include_faces,
                        'settings': include_settings
                    }
                }
                zf.writestr('manifest.json', json.dumps(manifest, indent=2))
                
                # Database backup
                if include_db and os.path.exists(self.db_path):
                    logger.info("Backing up database...")
                    # Create a hot backup
                    backup_db = self.backup_dir / 'temp_db.sqlite'
                    conn = sqlite3.connect(self.db_path)
                    backup_conn = sqlite3.connect(str(backup_db))
                    conn.backup(backup_conn)
                    backup_conn.close()
                    conn.close()
                    
                    zf.write(backup_db, 'database/facepro.db')
                    backup_db.unlink()
                
                # Faces directory
                if include_faces and self.faces_dir.exists():
                    logger.info("Backing up enrolled faces...")
                    for face_file in self.faces_dir.rglob('*'):
                        if face_file.is_file():
                            arcname = f"faces/{face_file.relative_to(self.faces_dir)}"
                            zf.write(face_file, arcname)
                
                # Settings
                if include_settings and self.config_path.exists():
                    logger.info("Backing up settings...")
                    zf.write(self.config_path, 'config/settings.json')
            
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info(f"Backup created: {backup_path} ({size_mb:.2f} MB)")
            
            return True, str(backup_path)
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            return False, str(e)
    
    def restore_backup(self, backup_path: str, 
                       restore_db: bool = True,
                       restore_faces: bool = True,
                       restore_settings: bool = True) -> Tuple[bool, str]:
        """
        Restore from a backup file.
        
        Warning: This will overwrite existing data!
        """
        if not os.path.exists(backup_path):
            return False, "Backup file not found"
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zf:
                # Read manifest
                manifest = json.loads(zf.read('manifest.json'))
                logger.info(f"Restoring backup from {manifest['created_at']}")
                
                temp_dir = self.backup_dir / 'temp_restore'
                zf.extractall(temp_dir)
                
                # Restore database
                if restore_db and (temp_dir / 'database' / 'facepro.db').exists():
                    logger.info("Restoring database...")
                    shutil.copy(
                        temp_dir / 'database' / 'facepro.db',
                        self.db_path
                    )
                
                # Restore faces
                if restore_faces and (temp_dir / 'faces').exists():
                    logger.info("Restoring faces...")
                    if self.faces_dir.exists():
                        shutil.rmtree(self.faces_dir)
                    shutil.copytree(temp_dir / 'faces', self.faces_dir)
                
                # Restore settings
                if restore_settings and (temp_dir / 'config' / 'settings.json').exists():
                    logger.info("Restoring settings...")
                    shutil.copy(
                        temp_dir / 'config' / 'settings.json',
                        self.config_path
                    )
                
                # Cleanup
                shutil.rmtree(temp_dir)
            
            logger.info("Restore completed successfully")
            return True, "Restore completed"
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False, str(e)
    
    def list_backups(self) -> list:
        """List available backups"""
        backups = []
        for f in self.backup_dir.glob('facepro_backup_*.zip'):
            stat = f.stat()
            backups.append({
                'name': f.name,
                'path': str(f),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def delete_old_backups(self, keep_count: int = 5):
        """Delete old backups, keeping the most recent `keep_count`"""
        backups = self.list_backups()
        
        for backup in backups[keep_count:]:
            try:
                os.unlink(backup['path'])
                logger.info(f"Deleted old backup: {backup['name']}")
            except Exception as e:
                logger.error(f"Failed to delete backup: {e}")
```

##### 4.2.4 Backup Wizard UI
```python
# Yeni fayl: src/ui/settings/dialogs/backup_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QProgressBar, QFileDialog,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.utils.backup_manager import BackupManager
from src.utils.i18n import tr

class BackupWorker(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, manager, include_db, include_faces, include_settings):
        super().__init__()
        self.manager = manager
        self.include_db = include_db
        self.include_faces = include_faces
        self.include_settings = include_settings
    
    def run(self):
        success, result = self.manager.create_backup(
            self.include_db, self.include_faces, self.include_settings
        )
        self.finished.emit(success, result)

class BackupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Backup & Restore")
        self.setMinimumSize(500, 400)
        
        self._manager = BackupManager()
        self._setup_ui()
        self._load_backups()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create Backup Section
        layout.addWidget(QLabel("<h3>Create Backup</h3>"))
        
        self._cb_database = QCheckBox("Database (enrolled faces, events)")
        self._cb_database.setChecked(True)
        layout.addWidget(self._cb_database)
        
        self._cb_faces = QCheckBox("Face images")
        self._cb_faces.setChecked(True)
        layout.addWidget(self._cb_faces)
        
        self._cb_settings = QCheckBox("Settings")
        self._cb_settings.setChecked(True)
        layout.addWidget(self._cb_settings)
        
        self._btn_backup = QPushButton("Create Backup")
        self._btn_backup.clicked.connect(self._create_backup)
        layout.addWidget(self._btn_backup)
        
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)
        
        # Existing Backups Section
        layout.addWidget(QLabel("<h3>Existing Backups</h3>"))
        
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Name", "Size", "Created"])
        layout.addWidget(self._table)
        
        btn_layout = QHBoxLayout()
        
        self._btn_restore = QPushButton("Restore Selected")
        self._btn_restore.clicked.connect(self._restore_backup)
        btn_layout.addWidget(self._btn_restore)
        
        self._btn_delete = QPushButton("Delete Selected")
        self._btn_delete.clicked.connect(self._delete_backup)
        btn_layout.addWidget(self._btn_delete)
        
        self._btn_import = QPushButton("Import Backup...")
        self._btn_import.clicked.connect(self._import_backup)
        btn_layout.addWidget(self._btn_import)
        
        layout.addLayout(btn_layout)
    
    def _load_backups(self):
        backups = self._manager.list_backups()
        self._table.setRowCount(len(backups))
        
        for i, backup in enumerate(backups):
            self._table.setItem(i, 0, QTableWidgetItem(backup['name']))
            self._table.setItem(i, 1, QTableWidgetItem(f"{backup['size_mb']} MB"))
            self._table.setItem(i, 2, QTableWidgetItem(backup['created']))
    
    def _create_backup(self):
        self._btn_backup.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)  # Indeterminate
        
        self._worker = BackupWorker(
            self._manager,
            self._cb_database.isChecked(),
            self._cb_faces.isChecked(),
            self._cb_settings.isChecked()
        )
        self._worker.finished.connect(self._on_backup_finished)
        self._worker.start()
    
    def _on_backup_finished(self, success, result):
        self._btn_backup.setEnabled(True)
        self._progress.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Success", f"Backup created:\n{result}")
            self._load_backups()
        else:
            QMessageBox.critical(self, "Error", f"Backup failed:\n{result}")
    
    def _restore_backup(self):
        # Implementation
        pass
    
    def _delete_backup(self):
        # Implementation
        pass
    
    def _import_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "", "ZIP Files (*.zip)"
        )
        if path:
            # Copy to backups dir and refresh
            pass
```

---

#### PROD-012: Performance Monitoring Dashboard (3 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 4.3.1 | Real-time FPS widget | | 0.5d | ✅ |
| 4.3.2 | Processing time chart | | 1d | ✅ |
| 4.3.3 | Memory usage monitoring | | 0.5d | ✅ |
| 4.3.4 | GPU utilization | | 0.5d | ✅ |
| 4.3.5 | Performance alerts | | 0.5d | ✅ |

**Detallar:**

##### 4.3.1-5 Performance Monitor Widget
```python
# Yeni fayl: src/ui/components/performance_monitor.py

import psutil
import time
from collections import deque
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

class PerformanceMonitor(QWidget):
    """Real-time performance monitoring widget"""
    
    performance_alert = pyqtSignal(str, str)  # metric, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # History
        self._fps_history = deque(maxlen=60)
        self._processing_time_history = deque(maxlen=60)
        self._memory_history = deque(maxlen=60)
        
        # Current values
        self._current_fps = 0.0
        self._current_processing_time = 0.0
        self._frame_times = deque(maxlen=30)
        
        # Thresholds
        self._fps_threshold = 10.0
        self._memory_threshold = 80.0  # percent
        
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        
        # FPS
        self._fps_label = QLabel("FPS: --")
        layout.addWidget(QLabel("🎬"), 0, 0)
        layout.addWidget(self._fps_label, 0, 1)
        
        # Processing Time
        self._proc_label = QLabel("Processing: -- ms")
        layout.addWidget(QLabel("⚡"), 1, 0)
        layout.addWidget(self._proc_label, 1, 1)
        
        # Memory
        self._mem_label = QLabel("Memory: -- MB")
        layout.addWidget(QLabel("💾"), 2, 0)
        layout.addWidget(self._mem_label, 2, 1)
        
        # CPU
        self._cpu_label = QLabel("CPU: --%")
        layout.addWidget(QLabel("🖥️"), 3, 0)
        layout.addWidget(self._cpu_label, 3, 1)
        
        # GPU (optional)
        self._gpu_label = QLabel("GPU: N/A")
        layout.addWidget(QLabel("🎮"), 4, 0)
        layout.addWidget(self._gpu_label, 4, 1)
    
    def _start_monitoring(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_stats)
        self._timer.start(1000)  # Update every second
    
    def _update_stats(self):
        # Memory
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        mem_percent = psutil.virtual_memory().percent
        self._memory_history.append(mem_mb)
        self._mem_label.setText(f"Memory: {mem_mb:.0f} MB ({mem_percent:.0f}%)")
        
        if mem_percent > self._memory_threshold:
            self.performance_alert.emit("memory", f"High memory usage: {mem_percent:.0f}%")
        
        # CPU
        cpu_percent = process.cpu_percent()
        self._cpu_label.setText(f"CPU: {cpu_percent:.0f}%")
        
        # FPS (from frame times)
        if self._frame_times:
            avg_frame_time = sum(self._frame_times) / len(self._frame_times)
            self._current_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        self._fps_history.append(self._current_fps)
        self._fps_label.setText(f"FPS: {self._current_fps:.1f}")
        
        if self._current_fps < self._fps_threshold and self._current_fps > 0:
            self.performance_alert.emit("fps", f"Low FPS: {self._current_fps:.1f}")
        
        # GPU (if available)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                self._gpu_label.setText(f"GPU: {gpu.load*100:.0f}% ({gpu.memoryUsed:.0f}MB)")
        except:
            pass
    
    def record_frame(self):
        """Call this when a frame is processed"""
        now = time.time()
        if hasattr(self, '_last_frame_time'):
            self._frame_times.append(now - self._last_frame_time)
        self._last_frame_time = now
    
    def record_processing_time(self, ms: float):
        """Record AI processing time"""
        self._current_processing_time = ms
        self._processing_time_history.append(ms)
        self._proc_label.setText(f"Processing: {ms:.0f} ms")
    
    def get_stats(self) -> dict:
        """Get current performance statistics"""
        return {
            'fps': self._current_fps,
            'avg_fps': sum(self._fps_history) / len(self._fps_history) if self._fps_history else 0,
            'processing_time_ms': self._current_processing_time,
            'memory_mb': self._memory_history[-1] if self._memory_history else 0,
        }
```

---

## 🧪 Test Planı

### Migration Tests
```python
def test_migration_runner_status():
    runner = MigrationRunner(':memory:')
    assert runner.get_current_version() == 0

def test_migration_applies():
    runner = MigrationRunner(':memory:')
    runner.migrate()
    assert runner.get_current_version() > 0

def test_migration_is_idempotent():
    runner = MigrationRunner(':memory:')
    runner.migrate()
    v1 = runner.get_current_version()
    runner.migrate()
    v2 = runner.get_current_version()
    assert v1 == v2
```

### Backup Tests
```python
def test_backup_create_and_restore():
    manager = BackupManager()
    success, path = manager.create_backup()
    assert success
    
    success, msg = manager.restore_backup(path)
    assert success
```

---

## ✅ Sprint Review Checklist

- [ ] Migration sistemi işləyir
- [ ] Auto-migration startup-da aktiv
- [ ] Backup wizard UI hazır
- [ ] Performance monitor dashboard-da göstərilir
- [ ] Bütün testlər keçir
- [ ] Documentation yeniləndi
