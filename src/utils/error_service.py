"""
FacePro Error Notification Service
-----------------------------------
User-facing error handling with toast notifications.
"""

from enum import Enum
from typing import Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

from src.utils.logger import get_logger

logger = get_logger()


class ErrorLevel(Enum):
    """Xəta səviyyələri."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """Xəta hadisəsi data class-ı."""
    level: ErrorLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"  # "camera", "ai", "database", "storage", "network"
    recoverable: bool = True
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ErrorNotificationService(QObject):
    """
    Singleton error notification service.
    
    Bütün tətbiq komponentlərindən xəta mesajları qəbul edir və
    UI-ya toast notification göndərir.
    
    Usage:
        from src.utils.error_service import get_error_service, ErrorLevel
        
        # Xəta bildirişi
        get_error_service().report_error(
            level=ErrorLevel.ERROR,
            title="Kamera bağlantısı uğursuz",
            message="IP kameraya qoşulmaq mümkün olmadı",
            source="camera_1",
            action_label="Yenidən cəhd et",
            action_callback=self._reconnect
        )
        
        # Xəta təmizlənməsi (problem həll oldu)
        get_error_service().clear_error("camera_1")
    """
    
    _instance = None
    
    # Signals
    error_occurred = pyqtSignal(object)  # ErrorEvent
    error_cleared = pyqtSignal(str)       # source
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        super().__init__()
        self._initialized = True
        self._error_history: List[ErrorEvent] = []
        self._active_errors: dict[str, ErrorEvent] = {}
        
        logger.info("ErrorNotificationService initialized")
    
    def report_error(
        self,
        level: ErrorLevel,
        title: str,
        message: str,
        source: str = "unknown",
        recoverable: bool = True,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ) -> ErrorEvent:
        """
        Xəta bildir.
        
        Args:
            level: Xəta səviyyəsi (INFO, WARNING, ERROR, CRITICAL)
            title: Qısa başlıq
            message: Ətraflı mesaj
            source: Mənbə identifikatoru (camera_1, ai, database, etc.)
            recoverable: Xəta bərpa oluna bilərmi?
            action_label: Action düyməsinin mətni (optional)
            action_callback: Action düyməsinə klik edildikdə çağırılan funksiya (optional)
            
        Returns:
            Yaradılan ErrorEvent
        """
        event = ErrorEvent(
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            recoverable=recoverable,
            action_label=action_label,
            action_callback=action_callback
        )
        
        # History-ə əlavə et
        self._error_history.append(event)
        
        # Max 500 event saxla
        if len(self._error_history) > 500:
            self._error_history = self._error_history[-500:]
        
        # Active errors yenilə
        self._active_errors[source] = event
        
        # Log
        log_message = f"[{source}] {title}: {message}"
        if level == ErrorLevel.CRITICAL:
            logger.critical(log_message)
        elif level == ErrorLevel.ERROR:
            logger.error(log_message)
        elif level == ErrorLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # UI-ya bildir
        self.error_occurred.emit(event)
        
        return event
    
    def clear_error(self, source: str):
        """
        Xətanı təmizlə (problem həll olundu).
        
        Args:
            source: Mənbə identifikatoru
        """
        if source in self._active_errors:
            del self._active_errors[source]
            self.error_cleared.emit(source)
            logger.info(f"Error cleared for source: {source}")
    
    def has_active_error(self, source: str) -> bool:
        """Mənbə üçün aktiv xəta varmı?"""
        return source in self._active_errors
    
    def get_active_error(self, source: str) -> Optional[ErrorEvent]:
        """Mənbə üçün aktiv xəta qaytar."""
        return self._active_errors.get(source)
    
    def get_all_active_errors(self) -> dict[str, ErrorEvent]:
        """Bütün aktiv xətalar."""
        return self._active_errors.copy()
    
    def get_history(self, limit: int = 100) -> List[ErrorEvent]:
        """
        Xəta tarixçəsini qaytar.
        
        Args:
            limit: Maksimum event sayı
            
        Returns:
            Son N xəta event-i
        """
        return self._error_history[-limit:]
    
    def get_history_by_source(self, source: str, limit: int = 50) -> List[ErrorEvent]:
        """Mənbə üzrə xəta tarixçəsi."""
        filtered = [e for e in self._error_history if e.source == source]
        return filtered[-limit:]
    
    def get_history_by_level(self, level: ErrorLevel, limit: int = 50) -> List[ErrorEvent]:
        """Səviyyə üzrə xəta tarixçəsi."""
        filtered = [e for e in self._error_history if e.level == level]
        return filtered[-limit:]
    
    def clear_history(self):
        """Bütün tarixçəni təmizlə."""
        self._error_history.clear()
        logger.info("Error history cleared")


# Global instance getter
_error_service: Optional[ErrorNotificationService] = None


def get_error_service() -> ErrorNotificationService:
    """Global ErrorNotificationService instance-ı qaytar."""
    global _error_service
    if _error_service is None:
        _error_service = ErrorNotificationService()
    return _error_service
