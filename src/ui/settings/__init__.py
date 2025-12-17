# FacePro Settings Module
# Modular settings dialog components

from .settings_dialog import SettingsDialog
from .dialogs.camera_dialog import CameraDialog
from .dialogs.camera_type_selector import CameraTypeSelector

__all__ = [
    'SettingsDialog',
    'CameraDialog',
    'CameraTypeSelector',
]
