"""
FacePro Helpers Module
Tətbiq üçün yardımçı funksiyalar.
- CV2 -> QPixmap çevirmə
- Şəkil ölçüləndirmə
- Konfiqurasiya oxuma/yazma
- Vaxt formatlaşdırma
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional, Tuple, Any, Dict, TYPE_CHECKING

# Optional imports for OpenCV and NumPy
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None

if TYPE_CHECKING:
    import numpy as np

from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

from .logger import get_logger

logger = get_logger()


# =============================================================================
# Image Conversion Functions
# =============================================================================

def cv2_to_qpixmap(cv_img: "np.ndarray", target_size: Optional[Tuple[int, int]] = None) -> QPixmap:
    """
    OpenCV şəklini PyQt6 QPixmap-a çevirir.
    
    Args:
        cv_img: OpenCV formatında şəkil (BGR)
        target_size: Opsional (width, height) tuple - ölçüləndirmə üçün
    
    Returns:
        QPixmap obyekti
    """
    try:
        # BGR -> RGB çevirmə
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        
        # Ölçüləndirmə (lazım olduqda)
        if target_size is not None:
            rgb_image = cv2.resize(rgb_image, target_size, interpolation=cv2.INTER_AREA)
        
        height, width, channel = rgb_image.shape
        bytes_per_line = channel * width
        
        # QImage yaratmaq
        q_image = QImage(
            rgb_image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )
        
        return QPixmap.fromImage(q_image)
    
    except Exception as e:
        logger.error(f"CV2 to QPixmap conversion failed: {e}")
        # Boş QPixmap qaytar
        return QPixmap()


if CV2_AVAILABLE:
    def resize_with_aspect_ratio(
        image,  # np.ndarray
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        inter: int = 3  # cv2.INTER_AREA = 3
    ):
        """
        Şəkli aspect ratio saxlayaraq ölçüləndirir.
        
        Args:
            image: OpenCV şəkli
            target_width: Hədəf eni (None olarsa height-dan hesablanır)
            target_height: Hədəf hündürlüyü (None olarsa width-dan hesablanır)
            inter: Interpolation metodu
        
        Returns:
            Ölçüləndirilmiş şəkil
        """
        height, width = image.shape[:2]
        
        if target_width is None and target_height is None:
            return image
        
        if target_width is None:
            ratio = target_height / float(height)
            new_dimensions = (int(width * ratio), target_height)
        else:
            ratio = target_width / float(width)
            new_dimensions = (target_width, int(height * ratio))
        
        return cv2.resize(image, new_dimensions, interpolation=inter)


    def crop_person(frame, bbox: Tuple[int, int, int, int], padding: int = 10):
        """
        Frame-dən şəxsi kəsib çıxarır (padding ilə).
        
        Args:
            frame: Əsas frame
            bbox: (x1, y1, x2, y2) bounding box
            padding: Kənarlardan əlavə piksel
        
        Returns:
            Kəsilmiş şəkil
        """
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        
        # Padding əlavə et (frame sərhədlərini aşmasın)
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        return frame[y1:y2, x1:x2].copy()
else:
    # Dummy functions when CV2 is not available
    def resize_with_aspect_ratio(*args, **kwargs):
        logger.warning("CV2 not available - resize_with_aspect_ratio skipped")
        return None
    
    def crop_person(*args, **kwargs):
        logger.warning("CV2 not available - crop_person skipped")
        return None


# =============================================================================
# Configuration Functions
# =============================================================================

def get_config_path() -> str:
    """Konfiqurasiya qovluğunun yolunu qaytarır."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config'
    )


def load_config(filename: str = 'settings.json') -> Dict[str, Any]:
    """
    JSON konfiqurasiya faylını oxuyur.
    
    Args:
        filename: Fayl adı (config qovluğunda)
    
    Returns:
        Konfiqurasiya dictionary-si
    """
    config_path = os.path.join(get_config_path(), filename)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.debug(f"Config loaded: {filename}")
            return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return {}


def save_config(data: Dict[str, Any], filename: str = 'settings.json') -> bool:
    """
    Konfiqurasiyanı JSON faylına yazır.
    
    Args:
        data: Saxlanılacaq data
        filename: Fayl adı (config qovluğunda)
    
    Returns:
        Uğurlu olub-olmadığı
    """
    config_path = os.path.join(get_config_path(), filename)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            logger.debug(f"Config saved: {filename}")
            return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def load_cameras() -> list:
    """Kamera siyahısını yükləyir."""
    config = load_config('cameras.json')
    return config.get('cameras', [])


def save_cameras(cameras: list) -> bool:
    """Kamera siyahısını saxlayır."""
    return save_config({'cameras': cameras}, 'cameras.json')


# =============================================================================
# Time & Date Functions  
# =============================================================================

def get_timestamp() -> str:
    """Cari timestamp-i string formatında qaytarır."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_date_stamp() -> str:
    """Cari tarixi string formatında qaytarır (fayl adları üçün)."""
    return datetime.now().strftime('%Y%m%d')


def get_datetime_stamp() -> str:
    """Cari tarix və vaxtı string formatında qaytarır (fayl adları üçün)."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def format_seconds(seconds: float) -> str:
    """Saniyələri oxunan formata çevirir (HH:MM:SS)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# =============================================================================
# File & Storage Functions
# =============================================================================

def get_folder_size_mb(folder_path: str) -> float:
    """
    Qovluğun ümumi ölçüsünü MB-da qaytarır.
    
    Args:
        folder_path: Qovluq yolu
    
    Returns:
        Ölçü MB-da
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.error(f"Failed to calculate folder size: {e}")
    
    return total_size / (1024 * 1024)


def ensure_dir(path: str) -> bool:
    """
    Qovluğun mövcudluğunu yoxlayır, yoxdursa yaradır.
    
    Args:
        path: Qovluq yolu
    
    Returns:
        Uğurlu olub-olmadığı
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def save_snapshot(
    frame, 
    folder: str = 'logs',
    prefix: str = 'snapshot'
) -> Optional[str]:
    """
    Frame-i JPG olaraq saxlayır.
    
    Args:
        frame: OpenCV formatında şəkil
        folder: 'logs' və ya 'faces'
        prefix: Fayl adı prefiksi
    
    Returns:
        Saxlanılan faylın yolu və ya None
    """
    if not CV2_AVAILABLE:
        logger.warning("CV2 not available - save_snapshot skipped")
        return None
    
    try:
        # Data qovluğu
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', folder
        )
        ensure_dir(data_dir)
        
        # Fayl adı
        filename = f"{prefix}_{get_datetime_stamp()}.jpg"
        filepath = os.path.join(data_dir, filename)
        
        # Saxla
        cv2.imwrite(filepath, frame)
        logger.debug(f"Snapshot saved: {filepath}")
        
        return filepath
    
    except Exception as e:
        logger.error(f"Failed to save snapshot: {e}")
        return None


# =============================================================================
# Network Functions
# =============================================================================

def check_internet_connection(host: str = "8.8.8.8", timeout: int = 3) -> bool:
    """
    İnternet bağlantısını yoxlayır (ping).
    
    Args:
        host: Yoxlanılacaq host
        timeout: Timeout saniyə
    
    Returns:
        Bağlantı varmı
    """
    import subprocess
    import platform
    
    try:
        # Windows vs Unix ping parametrləri
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        
        command = ['ping', param, '1', '-w', str(timeout * 1000), host]
        
        # Pəncərəni gizlət
        startupinfo = None
        creationflags = 0
        if platform.system().lower() == 'windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = subprocess.CREATE_NO_WINDOW
            
        result = subprocess.run(
            command, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1,
            startupinfo=startupinfo,
            creationflags=creationflags
        )
        
        return result.returncode == 0
    
    except Exception:
        return False


# =============================================================================
# RTSP URL Builder
# =============================================================================

def build_rtsp_url(
    ip: str,
    username: str = 'admin',
    password: str = '',
    port: int = 554,
    channel: int = 1,
    stream: int = 0,
    brand: str = 'hikvision'
) -> str:
    """
    Kamera brendinə görə RTSP URL yaradır.
    
    Args:
        ip: Kamera IP adresi
        username: İstifadəçi adı
        password: Şifrə
        port: RTSP portu (default: 554)
        channel: Kanal nömrəsi
        stream: Stream tipi (0: main, 1: sub)
        brand: Kamera brendi ('hikvision', 'dahua', 'generic')
    
    Returns:
        RTSP URL string
    """
    auth = f"{username}:{password}@" if password else f"{username}@"
    
    templates = {
        'hikvision': f"rtsp://{auth}{ip}:{port}/Streaming/Channels/{channel}0{stream + 1}",
        'dahua': f"rtsp://{auth}{ip}:{port}/cam/realmonitor?channel={channel}&subtype={stream}",
        'generic': f"rtsp://{auth}{ip}:{port}/stream{stream + 1}"
    }
    
    return templates.get(brand.lower(), templates['generic'])


if __name__ == "__main__":
    # Test
    print("Testing helpers...")
    
    # Config test
    config = load_config()
    print(f"Config loaded: {bool(config)}")
    
    # Internet test
    print(f"Internet connected: {check_internet_connection()}")
    
    # RTSP test
    url = build_rtsp_url("192.168.1.100", "admin", "password123", brand="hikvision")
    print(f"RTSP URL: {url}")
    
    print(f"Timestamp: {get_timestamp()}")

# =============================================================================
# Path Helpers
# =============================================================================

def get_app_root() -> str:
    """
    Tətbiqin kök qovluğunu qaytarır.
    PyInstaller ("frozen") və ya Source rejimini nəzərə alır.
    """
    import sys
    if getattr(sys, 'frozen', False):
        # EXE işləyir
        return os.path.dirname(sys.executable)
    else:
        # Source code işləyir (src/utils/helpers.py -> ../../)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))




def _ensure_db_initialized(db_path: str):
    """Cədvəlləri yaradır (əgər yoxdursa)."""
    import sqlite3
    
    # Fayl boşdursa və ya cədvəllər yoxdursa
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Face Encodings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                encoding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                object_label TEXT,
                confidence REAL,
                snapshot_path TEXT,
                identification_method TEXT DEFAULT 'unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migration: Add identification_method column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN identification_method TEXT DEFAULT 'unknown'")
        except:
            pass  # Column already exists
        
        # Re-ID Embeddings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reid_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                vector BLOB NOT NULL,
                confidence REAL,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Gait Embeddings table (Yeriş tanıma vektorları)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gait_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                confidence REAL DEFAULT 1.0,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Index for faster gait lookups by user_id
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gait_user ON gait_embeddings(user_id)
        """)
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize DB: {e}")


def get_db_path() -> str:
    """
    DB faylının tam yolunu qaytarır.
    Yol: {APP_ROOT}/data/db/facepro.db
    """
    root = get_app_root()
    db_path = os.path.join(root, "data", "db", "facepro.db")
    
    # Qovluq yoxdursa yarat (Parent qovluqlar)
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except:
        pass
        
    # DB strukturunu yoxla/yarat
    _ensure_db_initialized(db_path)
    
    return db_path

def get_faces_dir() -> str:
    """Faces qovluğunun tam yolunu qaytarır."""
    root = get_app_root()
    faces_dir = os.path.join(root, "data", "faces")
    try:
        os.makedirs(faces_dir, exist_ok=True)
    except:
        pass
    return faces_dir


def save_event(
    event_type: str,
    object_label: str = None,
    confidence: float = None,
    snapshot_path: str = None,
    identification_method: str = 'unknown'
) -> bool:
    """
    Event-i database-ə saxla.
    
    Args:
        event_type: Event növü ('PERSON', 'INTRUSION', 'OFFLINE_ALERT')
        object_label: Aşkarlanan obyektin adı ('Ali', 'Unknown', etc.)
        confidence: Tanıma etibar dərəcəsi (0.0 - 1.0)
        snapshot_path: Snapshot şəklinin yolu
        identification_method: Tanıma metodu ('face', 'reid', 'gait', 'unknown')
    
    Returns:
        bool: Uğurlu olduqda True
    """
    import sqlite3
    
    try:
        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (event_type, object_label, confidence, snapshot_path, identification_method)
            VALUES (?, ?, ?, ?, ?)
        """, (event_type, object_label, confidence, snapshot_path, identification_method))
        
        conn.commit()
        conn.close()
        logger.debug(f"Event saved: {event_type} - {object_label} ({identification_method})")
        return True
    except Exception as e:
        logger.error(f"Failed to save event: {e}")
        return False
