
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QFrame, QMessageBox
from PyQt6.QtCore import pyqtSignal
from src.utils.i18n import tr
from src.ui.styles import COLORS

class CameraSelectionDialog(QDialog):
    """
    Dialog for selecting a camera to display or adding a new one.
    """
    
    # Signals to communicate back to MainWindow
    camera_selected = pyqtSignal(str)
    add_local_camera_requested = pyqtSignal()
    add_rtsp_camera_requested = pyqtSignal()

    def __init__(self, parent=None, cameras_config=None):
        super().__init__(parent)
        self.setWindowTitle(tr('camera_dialog.select_type'))
        self.setMinimumWidth(350)
        self._cameras_config = cameras_config or []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 1. Available Cameras List
        if self._cameras_config:
            lbl = QLabel(tr('camera_dialog.available_cameras'))
            lbl.setStyleSheet("font-weight: bold; color: #a0a0a0;")
            layout.addWidget(lbl)
            
            for cam in self._cameras_config:
                cam_name = cam.get('name', 'Kamera')
                btn = QPushButton(f"📹 {cam_name}")
                btn.setProperty("class", "camera_list_btn")
                # Lambda capture fix: default argument n=cam_name
                btn.clicked.connect(lambda checked, n=cam_name: self._on_camera_clicked(n))
                layout.addWidget(btn)
                
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)
            line.setStyleSheet(f"background-color: {COLORS['border']}; margin: 10px 0;")
            layout.addWidget(line)
        
        # 2. Add New Camera
        lbl_new = QLabel(tr('camera_dialog.add_new_camera'))
        lbl_new.setStyleSheet("font-weight: bold; color: #a0a0a0;")
        layout.addWidget(lbl_new)
        
        local_btn = QPushButton(tr('camera_dialog.btn_local_camera'))
        local_btn.clicked.connect(self._on_local_clicked)
        layout.addWidget(local_btn)
        
        rtsp_btn = QPushButton(tr('camera_dialog.btn_rtsp_camera'))
        rtsp_btn.clicked.connect(self._on_rtsp_clicked)
        layout.addWidget(rtsp_btn)
        
        # Close button
        cancel_btn = QPushButton(tr('camera_dialog.cancel'))
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def _on_camera_clicked(self, name):
        self.camera_selected.emit(name)
        self.accept()

    def _on_local_clicked(self):
        self.add_local_camera_requested.emit()
        self.accept()

    def _on_rtsp_clicked(self):
        self.add_rtsp_camera_requested.emit()
        self.accept()
