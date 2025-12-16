# FacePro UI Module
# PyQt6 interfeys komponentlərini saxlayır

from .styles import DARK_THEME, COLORS, apply_theme, get_status_color
from .video_widget import VideoWidget, VideoGrid, StatusIndicator
from .settings_dialog import SettingsDialog, CameraDialog

# Note: MainWindow, LoginDialog, SetupWizardDialog are imported directly
# in main.py to avoid circular imports with auth_manager

__all__ = [
    # Styles
    'DARK_THEME', 'COLORS', 'apply_theme', 'get_status_color',
    # Video
    'VideoWidget', 'VideoGrid', 'StatusIndicator',
    # Dialogs
    'SettingsDialog', 'CameraDialog',
]

