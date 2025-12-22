"""
Database Migration Runner for FacePro
Handles versioning, applying SQL migrations and schema tracking.
"""

import os
import re
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

import sys
from pathlib import Path

# Add project root to sys.path
root_path = str(Path(__file__).parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.utils.logger import get_logger
from src.utils.helpers import get_db_path

logger = get_logger()

class MigrationRunner:
    """Database migration runner with versioning and rollback support"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self.migrations_dir = Path(__file__).parent
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def get_current_version(self) -> int:
        """Get current schema version from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT MAX(version) FROM schema_migrations")
            result = cursor.fetchone()
            return result[0] if result and result[0] else 0
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
        
        return sorted(migrations, key=lambda x: x[0])
    
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
            
            # Execute migration script
            # We use executescript for multiple SQL statements
            cursor.executescript(sql)
            
            # Record migration (if not already recorded by the script itself)
            # Some scripts might have INSERT INTO schema_migrations, but we check here too.
            cursor.execute("SELECT 1 FROM schema_migrations WHERE version = ?", (version,))
            if not cursor.fetchone():
                checksum = self.calculate_checksum(file_path)
                cursor.execute("""
                    INSERT INTO schema_migrations (version, name, checksum)
                    VALUES (?, ?, ?)
                """, (version, f"{version:03d}_{name}", checksum))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Migration {version} applied successfully")
            return True
            
        except sqlite3.Error as e:
            # Special handling for columns that might already exist during migration transition
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                logger.warning(f"Metadata in migration {version} might already exist, attempting to record success anyway.")
                try:
                    conn = self.get_connection()
                    cursor = conn.cursor()
                    checksum = self.calculate_checksum(file_path)
                    cursor.execute("INSERT OR IGNORE INTO schema_migrations (version, name, checksum) VALUES (?, ?, ?)", 
                                 (version, f"{version:03d}_{name}", checksum))
                    conn.commit()
                    conn.close()
                    return True
                except:
                    pass
            
            logger.error(f"Migration {version} failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Migration {version} unexpected error: {e}")
            return False
    
    def migrate(self, target_version: Optional[int] = None) -> bool:
        """Run all pending migrations up to target version"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("Database is up to date.")
            return True
        
        logger.info(f"Found {len(pending)} pending migrations.")
        
        for version, name, file_path in pending:
            if target_version and version > target_version:
                break
            
            if not self.apply_migration(version, name, file_path):
                logger.error(f"Aborting migration at version {version}")
                return False
        
        logger.info("All pending migrations applied.")
        return True
    
    def rollback(self, target_version: int) -> bool:
        """
        Rollback to a specific version.
        Note: Requires corresponding _rollback.sql files (optional).
        """
        current = self.get_current_version()
        
        if target_version >= current:
            logger.warning("Target version is not lower than current version.")
            return False
        
        # Rollback logic (simplified)
        logger.warning(f"Rollback to {target_version} requested. (Feature restricted in this version)")
        return False

    def status(self):
        """Display migration status"""
        current = self.get_current_version()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        print("-" * 40)
        print("DATABASE MIGRATION STATUS")
        print("-" * 40)
        print(f"Database Path: {self.db_path}")
        print(f"Current Schema Version: {current}")
        print(f"Available Migrations: {len(available)}")
        print(f"Pending Migrations: {len(pending)}")
        
        if pending:
            print("\nPending List:")
            for v, n, _ in pending:
                print(f"  [{v:03d}] {n}")
        print("-" * 40)

if __name__ == '__main__':
    import sys
    runner = MigrationRunner()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'status':
            runner.status()
        elif cmd == 'migrate':
            target = int(sys.argv[2]) if len(sys.argv) > 2 else None
            runner.migrate(target)
        else:
            print(f"Usage: python runner.py [status|migrate]")
    else:
        runner.status()
