"""
FacePro Dashboard Logs Page
System logs and event export.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, Qt

from src.utils.i18n import tr


class LogsPage(QWidget):
    """Logs Page with event list, filters and export button."""
    
    export_clicked = pyqtSignal()
    filter_changed = pyqtSignal(str)  # 'all', 'known', 'unknown'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_filter = 'all'
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup logs page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        self.title_lbl = QLabel(tr('logs_title'))
        self.title_lbl.setProperty("class", "welcome_text")
        layout.addWidget(self.title_lbl)
        
        # Filter Buttons Row
        filter_layout = QHBoxLayout()
        
        self.btn_all = QPushButton(tr('filter_all'))
        self.btn_all.setProperty("class", "filter_btn_active")
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self._set_filter('all'))
        filter_layout.addWidget(self.btn_all)
        
        self.btn_known = QPushButton(tr('filter_known'))
        self.btn_known.setProperty("class", "filter_btn")
        self.btn_known.setCheckable(True)
        self.btn_known.clicked.connect(lambda: self._set_filter('known'))
        filter_layout.addWidget(self.btn_known)
        
        self.btn_unknown = QPushButton(tr('filter_unknown'))
        self.btn_unknown.setProperty("class", "filter_btn")
        self.btn_unknown.setCheckable(True)
        self.btn_unknown.clicked.connect(lambda: self._set_filter('unknown'))
        filter_layout.addWidget(self.btn_unknown)
        
        filter_layout.addStretch()
        
        # Count label
        self.count_lbl = QLabel("0 " + tr('logs_entries'))
        self.count_lbl.setStyleSheet("color: #888; font-size: 12px;")
        filter_layout.addWidget(self.count_lbl)
        
        layout.addLayout(filter_layout)
        
        # Logs List
        self.logs_list = QListWidget()
        self.logs_list.setProperty("class", "activity_feed")
        layout.addWidget(self.logs_list)
        
        # Export Button
        self.btn_export = QPushButton(tr('export_csv'))
        self.btn_export.setProperty("class", "secondary")
        self.btn_export.clicked.connect(self.export_clicked.emit)
        layout.addWidget(self.btn_export)
    
    def _set_filter(self, filter_type: str):
        """Set active filter."""
        self._current_filter = filter_type
        
        # Update button states
        self.btn_all.setChecked(filter_type == 'all')
        self.btn_known.setChecked(filter_type == 'known')
        self.btn_unknown.setChecked(filter_type == 'unknown')
        
        # Update button styles
        self.btn_all.setProperty("class", "filter_btn_active" if filter_type == 'all' else "filter_btn")
        self.btn_known.setProperty("class", "filter_btn_active" if filter_type == 'known' else "filter_btn")
        self.btn_unknown.setProperty("class", "filter_btn_active" if filter_type == 'unknown' else "filter_btn")
        
        # Force style update
        self.btn_all.style().unpolish(self.btn_all)
        self.btn_all.style().polish(self.btn_all)
        self.btn_known.style().unpolish(self.btn_known)
        self.btn_known.style().polish(self.btn_known)
        self.btn_unknown.style().unpolish(self.btn_unknown)
        self.btn_unknown.style().polish(self.btn_unknown)
        
        # Apply filter to items
        self._apply_filter()
        
        self.filter_changed.emit(filter_type)
    
    def _apply_filter(self):
        """Apply current filter to show/hide items."""
        visible_count = 0
        
        for i in range(self.logs_list.count()):
            item = self.logs_list.item(i)
            widget = self.logs_list.itemWidget(item)
            
            if widget is None:
                continue
            
            # Get is_known property from widget
            is_known = getattr(widget, 'is_known', True)
            
            if self._current_filter == 'all':
                item.setHidden(False)
                visible_count += 1
            elif self._current_filter == 'known':
                item.setHidden(not is_known)
                if is_known:
                    visible_count += 1
            elif self._current_filter == 'unknown':
                item.setHidden(is_known)
                if not is_known:
                    visible_count += 1
        
        self.update_count(visible_count)
    
    def update_count(self, count: int):
        """Update entry count label."""
        self.count_lbl.setText(f"{count} {tr('logs_entries')}")
    
    def update_language(self):
        """Update text for live language change."""
        self.title_lbl.setText(tr('logs_title'))
        self.btn_export.setText(tr('export_csv'))
        self.btn_all.setText(tr('filter_all'))
        self.btn_known.setText(tr('filter_known'))
        self.btn_unknown.setText(tr('filter_unknown'))

