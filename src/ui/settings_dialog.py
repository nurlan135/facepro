"""
FacePro Settings Dialog Module
DEPRECATED: Bu fayl backward compatibility üçün saxlanılıb.
Yeni kod src/ui/settings/ modulundan istifadə etməlidir.

Refactoring: 919 sətir → 5 ayrı tab modulu + koordinator
"""

# Re-export from new modular location
from src.ui.settings import SettingsDialog, CameraDialog, CameraTypeSelector

__all__ = ['SettingsDialog', 'CameraDialog', 'CameraTypeSelector']
