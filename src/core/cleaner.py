"""
FacePro Cleaner Module (FIFO Storage Manager)
Disk dolduğunda ən köhnə faylları avtomatik silir.
"""

import os
import time
import threading
from typing import Optional, List, Tuple
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import load_config, get_folder_size_mb

logger = get_logger()


class StorageCleaner:
    """
    FIFO (First In, First Out) storage manager.
    Disk limiti aşıldığında ən köhnə faylları silir.
    """
    
    def __init__(self, target_folder: Optional[str] = None, max_size_gb: float = 10.0):
        """
        Args:
            target_folder: İzlənəcək qovluq yolu
            max_size_gb: Maksimum ölçü (GB)
        """
        self.max_size_gb = max_size_gb
        self.max_size_mb = max_size_gb * 1024
        
        # Default qovluq
        if target_folder is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.target_folder = os.path.join(base_dir, 'data', 'logs')
        else:
            self.target_folder = target_folder
        
        # Arxa plan thread-i üçün
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._check_interval = 600  # 10 dəqiqə (saniyə)
        
        logger.info(f"StorageCleaner initialized: {self.target_folder}, Max: {max_size_gb}GB")
    
    def get_files_sorted_by_age(self) -> List[Tuple[str, float]]:
        """
        Qovluqdakı faylları yaranma tarixinə görə sıralayır (köhnədən yeniyə).
        
        Returns:
            [(file_path, creation_time), ...] siyahısı
        """
        files = []
        
        try:
            for root, dirs, filenames in os.walk(self.target_folder):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    try:
                        ctime = os.path.getctime(filepath)
                        files.append((filepath, ctime))
                    except OSError:
                        continue
            
            # Köhnədən yeniyə sırala
            files.sort(key=lambda x: x[1])
            
        except Exception as e:
            logger.error(f"Failed to get files list: {e}")
        
        return files
    
    def cleanup(self) -> int:
        """
        Disk limitini yoxlayır və lazım olduqda köhnə faylları silir.
        
        Returns:
            Silinən faylların sayı
        """
        deleted_count = 0
        
        try:
            current_size_mb = get_folder_size_mb(self.target_folder)
            
            if current_size_mb <= self.max_size_mb:
                logger.debug(f"Storage OK: {current_size_mb:.1f}MB / {self.max_size_mb:.1f}MB")
                return 0
            
            logger.warning(f"Storage limit exceeded: {current_size_mb:.1f}MB / {self.max_size_mb:.1f}MB")
            
            # Faylları köhnədən yeniyə sırala
            files = self.get_files_sorted_by_age()
            
            # Limit altına düşənə qədər sil
            for filepath, ctime in files:
                try:
                    file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                    os.remove(filepath)
                    current_size_mb -= file_size
                    deleted_count += 1
                    
                    logger.info(f"Deleted old file: {os.path.basename(filepath)}")
                    
                    if current_size_mb <= self.max_size_mb * 0.9:  # 90%-ə qədər azalt
                        break
                        
                except OSError as e:
                    logger.error(f"Failed to delete {filepath}: {e}")
                    continue
            
            logger.info(f"Cleanup complete: {deleted_count} files deleted")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
        
        return deleted_count
    
    def start_background_cleanup(self, interval_minutes: int = 10):
        """
        Arxa planda periodik yoxlama başladır.
        
        Args:
            interval_minutes: Yoxlama intervalı (dəqiqə)
        """
        self._check_interval = interval_minutes * 60
        self._running = True
        self._schedule_next_cleanup()
        logger.info(f"Background cleanup started (every {interval_minutes} min)")
    
    def stop_background_cleanup(self):
        """Arxa plan yoxlamasını dayandırır."""
        self._running = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        logger.info("Background cleanup stopped")
    
    def _schedule_next_cleanup(self):
        """Növbəti cleanup-ı planlaşdırır."""
        if not self._running:
            return
        
        self._timer = threading.Timer(self._check_interval, self._background_cleanup)
        self._timer.daemon = True
        self._timer.start()
    
    def _background_cleanup(self):
        """Arxa plan cleanup callback-i."""
        try:
            self.cleanup()
        except Exception as e:
            logger.error(f"Background cleanup error: {e}")
        finally:
            self._schedule_next_cleanup()
    
    def get_status(self) -> dict:
        """
        Cari storage statusunu qaytarır.
        
        Returns:
            {
                'current_size_mb': float,
                'max_size_mb': float,
                'usage_percent': float,
                'file_count': int
            }
        """
        current_size = get_folder_size_mb(self.target_folder)
        file_count = sum(1 for _, _, files in os.walk(self.target_folder) for _ in files)
        
        return {
            'current_size_mb': round(current_size, 2),
            'max_size_mb': round(self.max_size_mb, 2),
            'usage_percent': round((current_size / self.max_size_mb) * 100, 1) if self.max_size_mb > 0 else 0,
            'file_count': file_count
        }


# Singleton instance
_cleaner_instance: Optional[StorageCleaner] = None


def get_cleaner() -> StorageCleaner:
    """Global cleaner instance qaytarır (lazy initialization)."""
    global _cleaner_instance
    
    if _cleaner_instance is None:
        config = load_config()
        storage_config = config.get('storage', {})
        max_size = storage_config.get('max_size_gb', 10.0)
        _cleaner_instance = StorageCleaner(max_size_gb=max_size)
    
    return _cleaner_instance


if __name__ == "__main__":
    # Test
    cleaner = get_cleaner()
    status = cleaner.get_status()
    print(f"Storage Status: {status}")
    
    # Manual cleanup test
    deleted = cleaner.cleanup()
    print(f"Deleted {deleted} files")
