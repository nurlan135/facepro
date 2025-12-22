"""
FacePro Settings - General Tab
Dil, tema və ümumi tətbiq ayarları.
"""

from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QCheckBox
)

from src.utils.i18n import tr


class GeneralTab(QWidget):
    """General settings tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # App Settings
        app_group = QGroupBox("Application")
        app_layout = QFormLayout(app_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Azərbaycanca", "English", "Русский"])
        app_layout.addRow(f"{tr('lbl_language')}:", self.language_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        app_layout.addRow(f"{tr('lbl_theme')}:", self.theme_combo)
        
        self.autostart_check = QCheckBox("Start with Windows")
        app_layout.addRow("", self.autostart_check)
        
        self.minimize_tray_check = QCheckBox("Minimize to system tray")
        app_layout.addRow("", self.minimize_tray_check)
        
        layout.addWidget(app_group)
        
        # Maintenance Section
        maint_group = QGroupBox("Baxım (Maintenance)")
        maint_layout = QVBoxLayout(maint_group)
        
        self.btn_backup_dialog = QPushButton(f"📁 {tr('btn_backup_restore') if tr('btn_backup_restore') != 'btn_backup_restore' else 'Backup və Geri Yükləmə'}")
        self.btn_backup_dialog.setProperty("class", "secondary")
        self.btn_backup_dialog.clicked.connect(self._open_backup_dialog)
        maint_layout.addWidget(self.btn_backup_dialog)
        
        layout.addWidget(maint_group)
        layout.addStretch()
    
    def _open_backup_dialog(self):
        """Backup dialoqunu açır."""
        from src.ui.settings.dialogs.backup_dialog import BackupDialog
        dialog = BackupDialog(self)
        dialog.exec()
    
    def load_settings(self, config: Dict[str, Any]):
        """Ayarları yükləyir."""
        ui_config = config.get('ui', {})
        
        theme = ui_config.get('theme', 'dark')
        self.theme_combo.setCurrentText(theme.capitalize())
        
        lang_code = ui_config.get('language', 'en')
        lang_map = {'az': 'Azərbaycanca', 'en': 'English', 'ru': 'Русский'}
        self.language_combo.setCurrentText(lang_map.get(lang_code, 'English'))
    
    def get_settings(self) -> Dict[str, Any]:
        """Ayarları qaytarır."""
        lang_map_inv = {'Azərbaycanca': 'az', 'English': 'en', 'Русский': 'ru'}
        
        return {
            'ui': {
                'theme': self.theme_combo.currentText().lower(),
                'language': lang_map_inv.get(self.language_combo.currentText(), 'en')
            }
        }
    
    def get_language_code(self) -> str:
        """Seçilmiş dil kodunu qaytarır."""
        lang_map_inv = {'Azərbaycanca': 'az', 'English': 'en', 'Русский': 'ru'}
        return lang_map_inv.get(self.language_combo.currentText(), 'en')
