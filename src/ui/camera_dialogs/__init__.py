"""
FacePro Camera Dialogs Module
RTSP konfiqurasiya və lokal kamera seçim dialoquları.

Refactored: 2025-12-17
- local_camera_selector.py: LocalCameraSelector class
- rtsp_config_dialog.py: RTSPConfigDialog class
"""

from .local_camera_selector import LocalCameraSelector
from .rtsp_config_dialog import RTSPConfigDialog

__all__ = ['LocalCameraSelector', 'RTSPConfigDialog']
