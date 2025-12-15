"""
FacePro Dashboard Module
Modular dashboard components.
"""

from .widgets import ActivityItem, ActionCard
from .sidebar import SidebarWidget
from .home_page import HomePage
from .camera_page import CameraPage
from .logs_page import LogsPage

__all__ = [
    'ActivityItem',
    'ActionCard', 
    'SidebarWidget',
    'HomePage',
    'CameraPage',
    'LogsPage'
]
