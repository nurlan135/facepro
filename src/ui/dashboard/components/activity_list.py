
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from src.ui.dashboard.widgets import ActivityItem

class ActivityListWidget(QListWidget):
    """
    Custom ListWidget for displaying activity events.
    Encapsulates item creation and duplicate handling.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "activity_feed")
        # Ensure focus policy doesn't trap keyboard if needed, or styling
        
    def add_event(self, label: str, time_str: str, is_known: bool, camera_name: str = "", at_top: bool = True):
        """
        Adds a new event to the list.
        at_top: If True, inserts at index 0 (Newest First). If False, appends (History).
        """
        item = QListWidgetItem()
        widget = ActivityItem(label, time_str, is_known, camera_name)
        item.setSizeHint(widget.sizeHint())
        
        if at_top:
            self.insertItem(0, item)
        else:
            self.addItem(item)
            
        self.setItemWidget(item, widget)

    def prepend_event(self, label: str, time_str: str, is_known: bool, camera_name: str = ""):
        """Helper for adding to top."""
        self.add_event(label, time_str, is_known, camera_name, at_top=True)
        
    def append_event(self, label: str, time_str: str, is_known: bool, camera_name: str = ""):
        """Helper for appending to bottom."""
        self.add_event(label, time_str, is_known, camera_name, at_top=False)
