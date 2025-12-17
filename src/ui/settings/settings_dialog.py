"""
FacePro Settings Dialog Module (Refactored)
Əsas ayarlar dialoqu - Tab koordinatoru.

Əvvəlki: 919 sətir
İndi: ~120 sətir
"""

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import pyqtSignal

from src.utils.logger import get_logger
from src.utils.helpers import load_config, save_config, load_cameras, save_cameras
from src.ui.styles import DARK_THEME
from src.utils.i18n import tr, set_language

# Modular tabs
from src.ui.settings.tabs import (
    GeneralTab, CamerasTab, AITab, NotificationsTab, StorageTab
)

logger = get_logger()


class SettingsDialog(QDialog):
    """Əsas ayarlar dialoqu - Tab koordinatoru."""
    
    settings_saved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._config = load_config()
        self._cameras = load_cameras()
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle(tr('settings_title'))
        self.setMinimumSize(600, 500)
        self.setStyleSheet(DARK_THEME)
        
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.general_tab = GeneralTab()
        self.cameras_tab = CamerasTab()
        self.ai_tab = AITab()
        self.notifications_tab = NotificationsTab()
        self.storage_tab = StorageTab()
        
        # Add tabs
        self.tabs.addTab(self.general_tab, tr('tab_general'))
        self.tabs.addTab(self.cameras_tab, tr('tab_camera'))
        self.tabs.addTab(self.ai_tab, tr('tab_ai'))
        self.tabs.addTab(self.notifications_tab, tr('tab_notifications'))
        self.tabs.addTab(self.storage_tab, tr('tab_storage'))
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(tr('btn_cancel'))
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)
        
        save_btn = QPushButton(tr('btn_save'))
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_settings(self):
        """Bütün tab-lara ayarları yükləyir."""
        self.general_tab.load_settings(self._config)
        self.cameras_tab.load_cameras(self._cameras)
        self.ai_tab.load_settings(self._config)
        self.notifications_tab.load_settings(self._config)
        self.storage_tab.load_settings(self._config)
    
    def _apply_settings(self):
        """Ayarları tətbiq edir."""
        # Collect settings from all tabs
        self._config.update(self.general_tab.get_settings())
        self._config.update(self.ai_tab.get_settings())
        self._config.update(self.notifications_tab.get_settings())
        self._config.update(self.storage_tab.get_settings())
        
        # Get cameras
        self._cameras = self.cameras_tab.get_cameras()
        
        # Save
        save_config(self._config)
        save_cameras(self._cameras)
        
        # Trigger live language update
        new_language = self.general_tab.get_language_code()
        set_language(new_language)
        
        self.settings_saved.emit()
        logger.info("Settings saved")
    
    def _save_and_close(self):
        """Ayarları saxla və bağla."""
        self._apply_settings()
        self.accept()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dialog = SettingsDialog()
    dialog.show()
    
    sys.exit(app.exec())
