"""
FacePro Configuration Models
Pydantic-based configuration validation models.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class TelegramConfig(BaseModel):
    """Telegram notification settings"""
    bot_token: str = ""
    chat_id: str = ""


class GSMConfig(BaseModel):
    """GSM modem settings"""
    enabled: bool = False
    com_port: str = "COM3"
    baud_rate: int = Field(default=9600, ge=1200, le=115200)
    phone_number: str = ""


class AIConfig(BaseModel):
    """AI detection settings"""
    motion_threshold: int = Field(default=25, ge=0, le=100)
    face_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    reid_confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    detection_classes: List[str] = ["person", "cat", "dog"]
    
    @field_validator('detection_classes')
    @classmethod
    def validate_classes(cls, v):
        allowed = {'person', 'cat', 'dog', 'car', 'truck'}
        for item in v:
            if item not in allowed:
                raise ValueError(f"Unknown detection class: {item}")
        return v


class GaitConfig(BaseModel):
    """Gait recognition settings"""
    enabled: bool = True
    threshold: float = Field(default=0.70, ge=0.50, le=0.95)
    sequence_length: int = Field(default=30, ge=20, le=60)


class StorageConfig(BaseModel):
    """Storage and FIFO settings"""
    max_size_gb: float = Field(default=10.0, ge=1.0, le=1000.0)
    recordings_path: str = "./data/logs/"
    faces_path: str = "./data/faces/"
    fifo_check_interval_minutes: int = Field(default=10, ge=1, le=60)


class CameraConfig(BaseModel):
    """Camera connection settings"""
    reconnect_interval_seconds: int = Field(default=5, ge=1, le=60)
    target_fps: int = Field(default=30, ge=1, le=60)
    frame_skip: int = Field(default=5, ge=1, le=30)


class UIConfig(BaseModel):
    """UI configuration"""
    theme: str = Field(default="dark", pattern=r"^(dark|light)$")
    language: str = Field(default="az", pattern=r"^(en|az|ru|tr)$")


class NotificationConfig(BaseModel):
    """Notification throttling settings"""
    max_per_minute: int = Field(default=10, ge=1, le=60)
    batch_unknown: bool = True
    batch_interval_seconds: int = Field(default=30, ge=5, le=300)
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "23:00"
    quiet_hours_end: str = "07:00"
    
    @field_validator('quiet_hours_start', 'quiet_hours_end')
    @classmethod
    def validate_time_format(cls, v):
        import re
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError(f"Invalid time format: {v}. Use HH:MM format.")
        return v


class AppConfig(BaseModel):
    """Root configuration model"""
    app_name: str = "FacePro"
    version: str = "1.0.0"
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    gsm: GSMConfig = Field(default_factory=GSMConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    gait: GaitConfig = Field(default_factory=GaitConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
