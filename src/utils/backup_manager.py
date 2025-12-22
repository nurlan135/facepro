"""
FacePro Backup Manager
Handles backup and restore operations for database, faces, and settings.
"""

import os
import shutil
import zipfile
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from src.utils.logger import get_logger
from src.utils.helpers import get_db_path, load_config, get_app_root, get_faces_dir

logger = get_logger()

class BackupManager:
    """Handles backup and restore operations"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        root = Path(get_app_root())
        self.backup_dir = Path(backup_dir) if backup_dir else root / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        self.db_path = get_db_path()
        self.faces_dir = Path(get_faces_dir())
        self.config_dir = root / 'config'
    
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
        backup_name = f"facepro_backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name
        
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
                    # Create a hot backup using SQLite online backup API
                    temp_db = self.backup_dir / f"temp_{timestamp}.db"
                    try:
                        source_conn = sqlite3.connect(self.db_path)
                        dest_conn = sqlite3.connect(str(temp_db))
                        source_conn.backup(dest_conn)
                        dest_conn.close()
                        source_conn.close()
                        
                        zf.write(temp_db, 'database/facepro.db')
                        temp_db.unlink()
                    except Exception as e:
                        logger.error(f"Database hot backup failed: {e}")
                        # Fallback to simple copy if hot backup fails
                        zf.write(self.db_path, 'database/facepro.db')
                
                # Faces directory
                if include_faces and self.faces_dir.exists():
                    logger.info("Backing up enrolled faces...")
                    for face_file in self.faces_dir.rglob('*'):
                        if face_file.is_file():
                            arcname = f"data/faces/{face_file.relative_to(self.faces_dir)}"
                            zf.write(face_file, arcname)
                
                # Settings (config directory)
                if include_settings and self.config_dir.exists():
                    logger.info("Backing up settings...")
                    for config_file in self.config_dir.glob('*.json'):
                        if config_file.is_file():
                            zf.write(config_file, f"config/{config_file.name}")
            
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            logger.info(f"Backup created: {backup_path.name} ({size_mb:.2f} MB)")
            
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
                try:
                    manifest_data = zf.read('manifest.json')
                    manifest = json.loads(manifest_data)
                    logger.info(f"Restoring backup created at {manifest['created_at']}")
                except:
                    logger.warning("Manifest not found or invalid in backup file")
                
                # List of files to extract for selective restore
                extract_list = []
                if restore_db:
                    extract_list.extend([f for f in zf.namelist() if f.startswith('database/')])
                if restore_faces:
                    extract_list.extend([f for f in zf.namelist() if f.startswith('data/faces/')])
                if restore_settings:
                    extract_list.extend([f for f in zf.namelist() if f.startswith('config/')])
                
                if not extract_list:
                    return False, "No items selected for restore or not found in backup"
                
                # Extract to temp directory first
                temp_restore_dir = self.backup_dir / 'temp_restore'
                if temp_restore_dir.exists():
                    shutil.rmtree(temp_restore_dir)
                temp_restore_dir.mkdir()
                
                zf.extractall(temp_restore_dir, members=extract_list)
                
                # Move files to their destinations
                if restore_db and (temp_restore_dir / 'database' / 'facepro.db').exists():
                    logger.info("Restoring database...")
                    os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                    shutil.copy2(temp_restore_dir / 'database' / 'facepro.db', self.db_path)
                
                if restore_faces and (temp_restore_dir / 'data' / 'faces').exists():
                    logger.info("Restoring faces...")
                    if self.faces_dir.exists():
                        shutil.rmtree(self.faces_dir)
                    shutil.copytree(temp_restore_dir / 'data' / 'faces', self.faces_dir)
                
                if restore_settings and (temp_restore_dir / 'config').exists():
                    logger.info("Restoring settings...")
                    for config_file in (temp_restore_dir / 'config').glob('*.json'):
                        shutil.copy2(config_file, self.config_dir / config_file.name)
                
                # Cleanup
                shutil.rmtree(temp_restore_dir)
                
            return True, "Restore completed successfully"
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False, f"Restore failed: {str(e)}"
    
    def list_backups(self) -> List[Dict]:
        """List available backups with metadata"""
        backups = []
        for f in self.backup_dir.glob('facepro_backup_*.zip'):
            stat = f.stat()
            backups.append({
                'name': f.name,
                'path': str(f),
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_at': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        # Sort by creation date descending
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup file"""
        try:
            path = self.backup_dir / backup_name
            if path.exists():
                path.unlink()
                logger.info(f"Backup deleted: {backup_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
