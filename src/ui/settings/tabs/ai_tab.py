"""
FacePro Settings - AI Tab
Motion, Face Recognition, Re-ID və Gait ayarları.
"""

from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox,
    QSpinBox, QDoubleSpinBox, QCheckBox
)

from src.utils.i18n import tr


class AITab(QWidget):
    """AI settings tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Motion Detection
        motion_group = QGroupBox("Motion Detection")
        motion_layout = QFormLayout(motion_group)
        
        self.motion_threshold_spin = QSpinBox()
        self.motion_threshold_spin.setRange(1, 100)
        self.motion_threshold_spin.setValue(25)
        motion_layout.addRow("Threshold:", self.motion_threshold_spin)
        
        layout.addWidget(motion_group)
        
        # Face Recognition
        face_group = QGroupBox("Face Recognition")
        face_layout = QFormLayout(face_group)
        
        self.face_confidence_spin = QDoubleSpinBox()
        self.face_confidence_spin.setRange(0.1, 1.0)
        self.face_confidence_spin.setSingleStep(0.05)
        self.face_confidence_spin.setValue(0.6)
        face_layout.addRow("Confidence:", self.face_confidence_spin)
        
        layout.addWidget(face_group)
        
        # Re-ID
        reid_group = QGroupBox("Person Re-ID")
        reid_layout = QFormLayout(reid_group)
        
        self.reid_confidence_spin = QDoubleSpinBox()
        self.reid_confidence_spin.setRange(0.1, 1.0)
        self.reid_confidence_spin.setSingleStep(0.05)
        self.reid_confidence_spin.setValue(0.75)
        reid_layout.addRow("Confidence:", self.reid_confidence_spin)
        
        layout.addWidget(reid_group)
        
        # Gait Recognition
        gait_group = QGroupBox(tr('gait_recognition'))
        gait_layout = QFormLayout(gait_group)
        
        self.gait_enabled_check = QCheckBox(tr('gait_enabled'))
        self.gait_enabled_check.setToolTip(tr('gait_settings'))
        gait_layout.addRow("", self.gait_enabled_check)
        
        self.gait_threshold_spin = QDoubleSpinBox()
        self.gait_threshold_spin.setRange(0.50, 0.95)
        self.gait_threshold_spin.setSingleStep(0.05)
        self.gait_threshold_spin.setValue(0.70)
        self.gait_threshold_spin.setToolTip(tr('gait_threshold_desc'))
        gait_layout.addRow(f"{tr('gait_threshold')}:", self.gait_threshold_spin)
        
        self.gait_sequence_spin = QSpinBox()
        self.gait_sequence_spin.setRange(20, 60)
        self.gait_sequence_spin.setValue(30)
        self.gait_sequence_spin.setSuffix(" frames")
        self.gait_sequence_spin.setToolTip(tr('gait_sequence_desc'))
        gait_layout.addRow(f"{tr('gait_sequence_length')}:", self.gait_sequence_spin)
        
        layout.addWidget(gait_group)
        layout.addStretch()
    
    def load_settings(self, config: Dict[str, Any]):
        """Ayarları yükləyir."""
        ai_config = config.get('ai', {})
        self.motion_threshold_spin.setValue(ai_config.get('motion_threshold', 25))
        self.face_confidence_spin.setValue(ai_config.get('face_confidence_threshold', 0.6))
        self.reid_confidence_spin.setValue(ai_config.get('reid_confidence_threshold', 0.75))
        
        gait_config = config.get('gait', {})
        self.gait_enabled_check.setChecked(gait_config.get('enabled', True))
        self.gait_threshold_spin.setValue(gait_config.get('threshold', 0.70))
        self.gait_sequence_spin.setValue(gait_config.get('sequence_length', 30))
    
    def get_settings(self) -> Dict[str, Any]:
        """Ayarları qaytarır."""
        return {
            'ai': {
                'motion_threshold': self.motion_threshold_spin.value(),
                'face_confidence_threshold': self.face_confidence_spin.value(),
                'reid_confidence_threshold': self.reid_confidence_spin.value(),
                'detection_classes': ['person', 'cat', 'dog']
            },
            'gait': {
                'enabled': self.gait_enabled_check.isChecked(),
                'threshold': self.gait_threshold_spin.value(),
                'sequence_length': self.gait_sequence_spin.value()
            }
        }
