"""
FacePro Settings - Cameras Tab
Kamera siyahısı və idarəetmə.
"""

from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt

from src.utils.logger import get_logger
from src.ui.camera_dialogs import RTSPConfigDialog, LocalCameraSelector
from src.ui.settings.dialogs.camera_type_selector import CameraTypeSelector
from src.ui.settings.dialogs.camera_dialog import CameraDialog

logger = get_logger()


class CamerasTab(QWidget):
    """Cameras settings tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cameras: List[Dict] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Camera list
        self.camera_list = QListWidget()
        layout.addWidget(self.camera_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Add Camera")
        add_btn.clicked.connect(self._add_camera)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self._edit_camera)
        btn_layout.addWidget(edit_btn)
        
        remove_btn = QPushButton("Remove")
        remove_btn.setProperty("class", "danger")
        remove_btn.clicked.connect(self._remove_camera)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def load_cameras(self, cameras: List[Dict]):
        """Kamera siyahısını yükləyir."""
        self._cameras = cameras.copy()
        self._refresh_list()
    
    def get_cameras(self) -> List[Dict]:
        """Kamera siyahısını qaytarır."""
        return self._cameras
    
    def _refresh_list(self):
        """Siyahını yeniləyir."""
        self.camera_list.clear()
        for camera in self._cameras:
            item = QListWidgetItem(f"{camera['name']} ({camera.get('type', 'Unknown')})")
            item.setData(Qt.ItemDataRole.UserRole, camera)
            self.camera_list.addItem(item)
    
    def _add_camera(self):
        """Yeni kamera əlavə edir."""
        type_selector = CameraTypeSelector(parent=self)
        if type_selector.exec() != QDialog.DialogCode.Accepted:
            return
        
        if type_selector.selected_type == "rtsp":
            dialog = RTSPConfigDialog(parent=self)
        else:
            dialog = LocalCameraSelector(parent=self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            camera_data = dialog.get_camera_data()
            if camera_data:
                self._cameras.append(camera_data)
                self._refresh_list()
                logger.info(f"Camera added: {camera_data.get('name', 'Unknown')}")
    
    def _edit_camera(self):
        """Seçilmiş kameranı redaktə edir."""
        item = self.camera_list.currentItem()
        if not item:
            return
        
        camera_data = item.data(Qt.ItemDataRole.UserRole)
        dialog = CameraDialog(camera_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            idx = self.camera_list.currentRow()
            self._cameras[idx] = dialog.get_camera_data()
            self._refresh_list()
    
    def _remove_camera(self):
        """Seçilmiş kameranı silir."""
        item = self.camera_list.currentItem()
        if not item:
            return
        
        reply = QMessageBox.question(
            self, "Confirm", "Are you sure you want to remove this camera?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            idx = self.camera_list.currentRow()
            del self._cameras[idx]
            self._refresh_list()
