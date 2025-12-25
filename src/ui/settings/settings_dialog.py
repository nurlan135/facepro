"""
FacePro Settings Dialog Module (Refactored)
Əsas ayarlar dialoqu - Tab koordinatoru.

Əvvəlki: 919 sətir
İndi: ~120 sətir
"""

from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt

from src.utils.logger import get_logger
from src.utils.helpers import load_config, save_config, load_cameras, save_cameras
from src.ui.styles import COLORS, CYBER_THEME

SETTINGS_STYLE = f"""
QTabWidget::pane {{
    border: 1px solid {COLORS.get('border_tech', '#333')};
    background: rgba(0, 0, 0, 0.2);
    top: -1px; 
}}
QTabBar::tab {{
    background: rgba(255, 255, 255, 0.05);
    color: {COLORS.get('text_muted', '#888')};
    border: 1px solid {COLORS.get('border_tech', '#333')};
    padding: 8px 16px;
    margin-right: 2px;
    font-family: 'Rajdhani', sans-serif;
    font-weight: bold;
    text-transform: uppercase;
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
}}
QTabBar::tab:selected {{
    background: {COLORS.get('bg_panel', '#000')};
    color: {COLORS.get('cyber_cyan', '#0FF')};
    border: 1px solid {COLORS.get('cyber_cyan', '#0FF')};
    border-bottom: none;
}}
QTabBar::tab:hover {{
    color: {COLORS.get('text_main', '#FFF')};
    background: rgba(255, 255, 255, 0.1);
}}

/* Group Box */
QGroupBox {{
    border: 1px solid {COLORS.get('border_tech', '#333')};
    margin-top: 2em; 
    padding: 20px 10px 10px 10px;
    font-family: 'Rajdhani', sans-serif;
    font-weight: bold;
    color: {COLORS.get('text_main', '#E0E0E0')};
    text-transform: uppercase;
    background: rgba(255, 255, 255, 0.02);
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left; 
    left: 10px;
    padding: 0 5px;
    color: {COLORS.get('cyber_cyan', '#0FF')};
    background-color: {COLORS.get('bg_panel', '#000')}; /* Mask the border behind */
}}

/* Form Controls */
QLabel {{
    color: {COLORS.get('text_main', '#E0E0E0')};
    padding-right: 10px;
}}

QCheckBox {{
    spacing: 8px;
    color: {COLORS.get('text_main', '#E0E0E0')};
    padding: 5px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS.get('text_muted', '#888')};
    background: rgba(0,0,0,0.5);
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS.get('cyber_cyan', '#0FF')};
    border-color: {COLORS.get('cyber_cyan', '#0FF')};
}}

QComboBox {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid {COLORS.get('border_tech', '#555')};
    color: {COLORS.get('text_main', '#FFF')};
    padding: 8px;
    min-width: 150px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background: {COLORS.get('bg_panel', '#000')};
    border: 1px solid {COLORS.get('cyber_cyan', '#0FF')};
    selection-background-color: {COLORS.get('cyber_cyan', '#0FF')};
    color: white;
}}

/* Table Widget Styling (for Audit Logs) */
QTableWidget {{
    background-color: rgba(255, 255, 255, 0.02);
    color: {COLORS.get('text_main', '#e0e0e0')};
    border: 1px solid {COLORS.get('border_tech', '#333')};
    gridline-color: {COLORS.get('grid_line', '#222')};
    font-family: 'Consolas', monospace;
    font-size: 13px;
    outline: none;
}}
QTableWidget::item {{
    padding: 6px;
    border-bottom: 1px solid rgba(0, 240, 255, 0.05);
}}
QTableWidget::item:focus {{
    outline: none;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: rgba(0, 240, 255, 0.2);
    color: white;
    border: 1px solid {COLORS.get('cyber_cyan', '#00f0ff')};
}}
QHeaderView::section {{
    background-color: {COLORS.get('bg_panel', '#000')};
    color: {COLORS.get('cyber_cyan', '#00FFFF')};
    padding: 8px;
    border: none;
    border-bottom: 2px solid {COLORS.get('cyber_cyan', '#00FFFF')};
    font-family: 'Rajdhani', sans-serif;
    font-weight: bold;
    text-transform: uppercase;
}}
QScrollBar:vertical {{
    border: none;
    background: {COLORS.get('bg_void', '#000')};
    width: 6px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS.get('border_tech', '#333')};
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS.get('cyber_cyan', '#0FF')};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* General Buttons inside tabs */
QPushButton {{
    background: transparent;
    border: 1px solid {COLORS.get('cyber_cyan', '#0FF')};
    color: {COLORS.get('cyber_cyan', '#0FF')};
    padding: 8px 15px;
    font-family: 'Rajdhani', sans-serif;
    text-transform: uppercase;
    font-weight: bold;
}}
QPushButton:hover {{
    background: rgba(0, 240, 255, 0.1);
    color: white;
}}
"""
from src.utils.i18n import tr, set_language

# Modular tabs
from src.ui.settings.tabs import (
    GeneralTab, CamerasTab, AITab, NotificationsTab, StorageTab, AuditTab
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
        self.setMinimumSize(800, 600)
        self.setStyleSheet(CYBER_THEME + SETTINGS_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Tab Widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.general_tab = GeneralTab()
        self.cameras_tab = CamerasTab()
        self.ai_tab = AITab()
        self.notifications_tab = NotificationsTab()
        self.storage_tab = StorageTab()
        self.audit_tab = AuditTab()
        
        # Add tabs
        self.tabs.addTab(self.general_tab, tr('tab_general').upper())
        self.tabs.addTab(self.cameras_tab, tr('tab_camera').upper())
        self.tabs.addTab(self.ai_tab, tr('tab_ai').upper())
        self.tabs.addTab(self.notifications_tab, tr('tab_notifications').upper())
        self.tabs.addTab(self.storage_tab, tr('tab_storage').upper())
        self.tabs.addTab(self.audit_tab, tr('tab_audit').upper())
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.addStretch()
        
        cancel_btn = QPushButton(tr('btn_cancel').upper())
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS.get('border_tech', '#333')};
                color: {COLORS.get('text_muted', '#888')};
                padding: 10px 20px;
                font-weight: bold;
                font-family: 'Rajdhani', sans-serif;
            }}
            QPushButton:hover {{
                border-color: {COLORS.get('text_main', '#FFF')};
                color: {COLORS.get('text_main', '#FFF')};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton(f"✓ {tr('btn_apply').upper()}")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {COLORS.get('cyber_cyan', '#0FF')};
                color: {COLORS.get('cyber_cyan', '#0FF')};
                padding: 10px 20px;
                font-weight: bold;
                font-family: 'Rajdhani', sans-serif;
            }}
            QPushButton:hover {{
                background: rgba(0, 240, 255, 0.1);
            }}
        """)
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)
        
        save_btn = QPushButton(f"💾 {tr('btn_save').upper()}")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.get('acid_green', '#0F0')};
                color: black;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                font-family: 'Rajdhani', sans-serif;
            }}
            QPushButton:hover {{
                background-color: #B3FF00;
            }}
        """)
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
        self.audit_tab.load_settings(self._config)
    
    def _apply_settings(self):
        """Ayarları tətbiq edir."""
        from PyQt6.QtWidgets import QMessageBox
        from src.utils.config_models import AppConfig
        from pydantic import ValidationError
        
        # New temp config to validate
        new_config = self._config.copy()
        
        # Collect settings from all tabs
        new_config.update(self.general_tab.get_settings())
        new_config.update(self.ai_tab.get_settings())
        new_config.update(self.notifications_tab.get_settings())
        new_config.update(self.storage_tab.get_settings())
        
        # Validate with Pydantic
        try:
            AppConfig(**new_config)
            # If valid, update original config
            self._config = new_config
        except ValidationError as e:
            error_msg = "\n".join([f"- {err['loc'][0]}: {err['msg']}" for err in e.errors()])
            QMessageBox.warning(
                self, 
                tr('error'), 
                f"Konfiqurasiya yoxlanışı uğursuz oldu:\n{error_msg}"
            )
            return
            
        # Get cameras
        self._cameras = self.cameras_tab.get_cameras()
        
        # Save
        save_config(self._config)
        save_cameras(self._cameras)
        
        # Audit Log
        from src.utils.audit_logger import get_audit_logger
        get_audit_logger().log("SETTINGS_CHANGE", {"tabs_updated": "all"})
        
        # Trigger live language update
        new_language = self.general_tab.get_language_code()
        set_language(new_language)
        
        self.settings_saved.emit()
        logger.info("Settings saved and validated")
    
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
