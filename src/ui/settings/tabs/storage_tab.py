"""
FacePro Settings - Storage Tab
FIFO saxlama və disk ayarları.
"""

from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QSpinBox
)


class StorageTab(QWidget):
    """Storage settings tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Storage Settings
        storage_group = QGroupBox("Storage Settings")
        storage_layout = QFormLayout(storage_group)
        
        self.max_storage_spin = QSpinBox()
        self.max_storage_spin.setRange(1, 1000)
        self.max_storage_spin.setSuffix(" GB")
        self.max_storage_spin.setValue(10)
        storage_layout.addRow("Max Storage:", self.max_storage_spin)
        
        self.cleanup_interval_spin = QSpinBox()
        self.cleanup_interval_spin.setRange(1, 60)
        self.cleanup_interval_spin.setSuffix(" min")
        self.cleanup_interval_spin.setValue(10)
        storage_layout.addRow("Cleanup Interval:", self.cleanup_interval_spin)
        
        layout.addWidget(storage_group)
        layout.addStretch()
    
    def load_settings(self, config: Dict[str, Any]):
        """Ayarları yükləyir."""
        storage_config = config.get('storage', {})
        self.max_storage_spin.setValue(int(storage_config.get('max_size_gb', 10)))
        self.cleanup_interval_spin.setValue(storage_config.get('fifo_check_interval_minutes', 10))
    
    def get_settings(self) -> Dict[str, Any]:
        """Ayarları qaytarır."""
        return {
            'storage': {
                'max_size_gb': self.max_storage_spin.value(),
                'recordings_path': './data/logs/',
                'faces_path': './data/faces/',
                'fifo_check_interval_minutes': self.cleanup_interval_spin.value()
            }
        }
