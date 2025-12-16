# FacePro UI Module
# PyQt6 interfeys komponentlərini saxlayır

from .styles import DARK_THEME, COLORS, apply_theme, get_status_color
from .video_widget import VideoWidget, VideoGrid, StatusIndicator
from .settings_dialog import SettingsDialog, CameraDialog
from .main_window import MainWindow
from .login_dialog import LoginDialog, show_login_dialog

__all__ = [
    # Styles
    'DARK_THEME', 'COLORS', 'apply_theme', 'get_status_color',
    # Video
    'VideoWidget', 'VideoGrid', 'StatusIndicator',
    # Dialogs
    'SettingsDialog', 'CameraDialog', 'LoginDialog', 'show_login_dialog',
    # Main
    'MainWindow',
]

