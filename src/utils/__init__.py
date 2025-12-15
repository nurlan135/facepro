# FacePro Utils Module
# Yardımçı funksiyalar və logging sistemini saxlayır

from .logger import get_logger, debug, info, warning, error, critical, exception

# Import only non-CV2 dependent functions first
from .helpers import (
    # Config
    load_config,
    save_config,
    load_cameras,
    save_cameras,
    # Time
    get_timestamp,
    get_date_stamp,
    get_datetime_stamp,
    format_seconds,
    # Storage
    get_folder_size_mb,
    ensure_dir,
    # Network
    check_internet_connection,
    build_rtsp_url,
    # CV2 availability flag
    CV2_AVAILABLE,
)

# CV2-dependent functions (optional import)
if CV2_AVAILABLE:
    from .helpers import (
        cv2_to_qpixmap,
        resize_with_aspect_ratio,
        crop_person,
        save_snapshot,
    )
else:
    # Dummy functions when CV2 is not available
    def cv2_to_qpixmap(*args, **kwargs):
        from PyQt6.QtGui import QPixmap
        return QPixmap()
    
    def resize_with_aspect_ratio(*args, **kwargs):
        return None
    
    def crop_person(*args, **kwargs):
        return None
    
    def save_snapshot(*args, **kwargs):
        return None

__all__ = [
    # Logger
    'get_logger', 'debug', 'info', 'warning', 'error', 'critical', 'exception',
    # Helpers
    'cv2_to_qpixmap', 'resize_with_aspect_ratio', 'crop_person', 'save_snapshot',
    'load_config', 'save_config', 'load_cameras', 'save_cameras',
    'get_timestamp', 'get_date_stamp', 'get_datetime_stamp', 'format_seconds',
    'get_folder_size_mb', 'ensure_dir',
    'check_internet_connection', 'build_rtsp_url',
    'CV2_AVAILABLE',
]
