"""
FacePro Main Window Module
Əsas Dashboard UI pəncərəsi.
"""

from typing import Optional, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QMenuBar, QMenu,
    QSplitter, QListWidget, QListWidgetItem, QFrame,
    QToolBar, QMessageBox, QFileDialog, QSystemTrayIcon
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QPixmap

# Optional imports for OpenCV and NumPy
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None

import sys
import os
import sqlite3
import csv
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import (
    load_config, load_cameras, save_snapshot, 
    check_internet_connection, get_timestamp
)
from src.ui.styles import DARK_THEME, COLORS, apply_theme
from src.ui.video_widget import VideoWidget, VideoGrid, StatusIndicator
from src.ui.settings_dialog import SettingsDialog
from src.ui.face_enrollment import FaceEnrollmentDialog, ManageFacesDialog
from src.core.camera_thread import CameraWorker, CameraConfig, CameraManager
from src.core.ai_thread import AIWorker, FrameResult, Detection, DetectionType, draw_detections
from src.core.cleaner import get_cleaner
from src.hardware.telegram_notifier import get_telegram_notifier

logger = get_logger()


class EventListItem(QWidget):
    """Hadisə siyahısı elementi."""
    
    def __init__(self, event_data: Dict, parent=None):
        super().__init__(parent)
        
        self._event_data = event_data
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(60, 45)
        self.thumbnail.setStyleSheet(f"""
            background-color: {COLORS['bg_light']};
            border-radius: 4px;
        """)
        
        if 'snapshot' in self._event_data and self._event_data['snapshot'] is not None:
            # Show thumbnail
            pass
        
        layout.addWidget(self.thumbnail)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Label
        label = QLabel(self._event_data.get('label', 'Unknown'))
        label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold;")
        info_layout.addWidget(label)
        
        # Time
        time_str = self._event_data.get('time', datetime.now().strftime('%H:%M:%S'))
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Confidence
        confidence = self._event_data.get('confidence', 0)
        conf_label = QLabel(f"{confidence:.0%}")
        conf_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(conf_label)


class StatusPanel(QWidget):
    """Alt status paneli."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        
        # Update timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_status)
        self._timer.start(5000)  # Her 5 saniye
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # CPU
        self.cpu_label = QLabel("CPU: --")
        self.cpu_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.cpu_label)
        
        layout.addWidget(self._separator())
        
        # RAM
        self.ram_label = QLabel("RAM: --")
        self.ram_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.ram_label)
        
        layout.addWidget(self._separator())
        
        # Storage
        self.storage_label = QLabel("Storage: --")
        self.storage_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.storage_label)
        
        layout.addStretch()
        
        # Internet Status
        self.internet_indicator = StatusIndicator()
        layout.addWidget(self.internet_indicator)
        
        self.internet_label = QLabel("Internet")
        self.internet_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.internet_label)
        
        layout.addWidget(self._separator())
        
        # Telegram Status
        self.telegram_indicator = StatusIndicator()
        layout.addWidget(self.telegram_indicator)
        
        self.telegram_label = QLabel("Telegram")
        self.telegram_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.telegram_label)
        
        layout.addWidget(self._separator())
        
        # GSM Status
        self.gsm_indicator = StatusIndicator()
        layout.addWidget(self.gsm_indicator)
        
        self.gsm_label = QLabel("GSM")
        self.gsm_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.gsm_label)
    
    def _separator(self) -> QFrame:
        """Vertical separator yaradır."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        return sep
    
    def _update_status(self):
        """Status yeniləyir."""
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent()
            self.cpu_label.setText(f"CPU: {cpu_percent:.0f}%")
            
            # RAM
            memory = psutil.virtual_memory()
            self.ram_label.setText(f"RAM: {memory.percent:.0f}%")
            
        except ImportError:
            pass
        
        # Storage
        cleaner = get_cleaner()
        status = cleaner.get_status()
        self.storage_label.setText(f"Storage: {status['current_size_mb']:.0f}MB / {status['max_size_mb']:.0f}MB")
        
        # Internet
        internet_ok = check_internet_connection()
        self.internet_indicator.set_status('online' if internet_ok else 'offline')
    
    def set_gsm_status(self, connected: bool):
        """GSM statusunu ayarlar."""
        self.gsm_indicator.set_status('online' if connected else 'offline')


class MainWindow(QMainWindow):
    """FacePro Əsas Pəncərəsi."""
    
    def __init__(self):
        super().__init__()
        
        self._config = load_config()
        self._cameras_config = load_cameras()
        
        # Managers
        self._camera_manager = CameraManager()
        self._ai_worker: Optional[AIWorker] = None
        self._telegram_notifier = get_telegram_notifier()
        
        # State
        self._is_running = False
        
        self._setup_ui()
        self._setup_menu()
        self._setup_connections()
        
        logger.info("MainWindow initialized")
    
    def _setup_ui(self):
        """UI setup."""
        self.setWindowTitle("FacePro - Smart Security System")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(DARK_THEME)
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Splitter (Video Grid | Events Panel)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        
        # Video Grid
        self.video_grid = VideoGrid()
        splitter.addWidget(self.video_grid)
        
        # Events Panel
        events_panel = self._create_events_panel()
        splitter.addWidget(events_panel)
        
        # Splitter ratio (70% video, 30% events)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter, 1)
        
        # Status Panel
        self.status_panel = StatusPanel()
        main_layout.addWidget(self.status_panel)
    
    def _create_toolbar(self) -> QWidget:
        """Toolbar yaradır."""
        toolbar = QWidget()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet(f"background-color: {COLORS['bg_medium']};")
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Logo / Title
        title = QLabel("FacePro")
        title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Control Buttons
        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedWidth(100)
        self.start_btn.clicked.connect(self._toggle_running)
        layout.addWidget(self.start_btn)
        
        # Settings Button
        settings_btn = QPushButton("Settings")
        settings_btn.setProperty("class", "secondary")
        settings_btn.setFixedWidth(100)
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)
        
        return toolbar
    
    def _create_events_panel(self) -> QWidget:
        """Hadisələr panelini yaradır."""
        panel = QWidget()
        panel.setStyleSheet(f"background-color: {COLORS['bg_medium']};")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Recent Events")
        header.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 14px;
            font-weight: bold;
            padding-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Events List
        self.events_list = QListWidget()
        self.events_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QListWidget::item {{
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        layout.addWidget(self.events_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self._clear_events)
        btn_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("Export")
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self._export_events)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)
        
        return panel
    
    def _setup_menu(self):
        """Menu bar yaradır."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View Menu
        view_menu = menubar.addMenu("View")
        
        grid_1_action = QAction("1 Camera", self)
        grid_1_action.triggered.connect(lambda: self.video_grid.set_columns(1))
        view_menu.addAction(grid_1_action)
        
        grid_2_action = QAction("2x2 Grid", self)
        grid_2_action.triggered.connect(lambda: self.video_grid.set_columns(2))
        view_menu.addAction(grid_2_action)
        
        grid_3_action = QAction("3x3 Grid", self)
        grid_3_action.triggered.connect(lambda: self.video_grid.set_columns(3))
        view_menu.addAction(grid_3_action)
        
        # Faces Menu
        faces_menu = menubar.addMenu("Faces")
        
        add_face_action = QAction("Add Known Face", self)
        add_face_action.triggered.connect(self._add_known_face)
        faces_menu.addAction(add_face_action)
        
        manage_faces_action = QAction("Manage Faces", self)
        manage_faces_action.triggered.connect(self._manage_faces)
        faces_menu.addAction(manage_faces_action)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_connections(self):
        """Signal/slot bağlantıları."""
        pass
    
    def _toggle_running(self):
        """Sistemi başlat/dayandır."""
        if self._is_running:
            self._stop_system()
        else:
            self._start_system()
    
    def _start_system(self):
        """Sistemi başladır."""
        logger.info("Starting system...")
        
        # AI Worker başlat
        self._ai_worker = AIWorker()
        self._ai_worker.frame_processed.connect(self._on_frame_processed)
        self._ai_worker.detection_alert.connect(self._on_detection_alert)
        self._ai_worker.start()
        
        # Kameraları başlat
        self._cameras_config = load_cameras()
        
        for cam_data in self._cameras_config:
            config = CameraConfig(
                source=cam_data['source'],
                name=cam_data['name'],
                target_fps=self._config.get('camera', {}).get('target_fps', 30)
            )
            
            # Video widget əlavə et
            video_widget = self.video_grid.add_camera_view(config.name)
            
            # Camera worker əlavə et və başlat
            worker = self._camera_manager.add_camera(config)
            worker.frame_ready.connect(self._on_camera_frame)
            worker.connection_status.connect(self._on_camera_status)
            worker.start()
        
        # Storage cleaner başlat
        cleaner = get_cleaner()
        cleaner.start_background_cleanup()
        
        self._is_running = True
        self.start_btn.setText("Stop")
        self.start_btn.setStyleSheet(f"background-color: {COLORS['danger']};")
        
        # Telegram bildirişi
        if self._telegram_notifier.is_enabled:
            self._telegram_notifier.send_startup_message()
            self.status_panel.telegram_indicator.set_status('online')
        
        logger.info("System started")
    
    def _stop_system(self):
        """Sistemi dayandırır."""
        logger.info("Stopping system...")
        
        # AI worker dayandır
        if self._ai_worker:
            self._ai_worker.stop()
            self._ai_worker = None
        
        # Kameraları dayandır
        self._camera_manager.stop_all()
        
        # Storage cleaner dayandır
        cleaner = get_cleaner()
        cleaner.stop_background_cleanup()
        
        self._is_running = False
        self.start_btn.setText("Start")
        self.start_btn.setStyleSheet("")
        
        # Telegram bildirişi
        if self._telegram_notifier.is_enabled:
            self._telegram_notifier.send_shutdown_message()
            self.status_panel.telegram_indicator.set_status('offline')
        
        logger.info("System stopped")
    
    @pyqtSlot(np.ndarray, str)
    def _on_camera_frame(self, frame: np.ndarray, camera_name: str):
        """Kamera frame-i alındıqda."""
        # AI-a göndər
        if self._ai_worker:
            self._ai_worker.process_frame(frame, camera_name)
    
    @pyqtSlot(bool, str)
    def _on_camera_status(self, connected: bool, camera_name: str):
        """Kamera bağlantı statusu dəyişdikdə."""
        widget = self.video_grid.get_widget(camera_name)
        if widget:
            widget.set_connected(connected)
    
    @pyqtSlot(object)
    def _on_frame_processed(self, result: FrameResult):
        """AI frame emalı tamamlandıqda."""
        # Detection-ları çək
        annotated_frame = draw_detections(result.frame, result.detections)
        
        # Video widget-i yenilə
        self.video_grid.update_frame(result.camera_name, annotated_frame)
    
    @pyqtSlot(object, np.ndarray)
    def _on_detection_alert(self, detection: Detection, frame: np.ndarray):
        """Yeni detection alert-i."""
        # Event əlavə et
        event_data = {
            'label': detection.label or detection.type.value,
            'confidence': detection.confidence,
            'time': get_timestamp(),
            'snapshot': frame
        }
        
        self._add_event(event_data)
        
        # Snapshot saxla
        snapshot_path = save_snapshot(frame, prefix=detection.label or 'unknown')
        
        # Log to Database
        self._log_event_to_db(
            event_type="PERSON" if detection.type == DetectionType.PERSON else "OTHER",
            object_label=detection.label or "Unknown",
            confidence=detection.confidence,
            snapshot_path=snapshot_path
        )
        
        # Telegram bildirişi
        self._telegram_notifier.send_detection_alert(
            frame=frame,
            label=detection.label or 'Unknown',
            confidence=detection.confidence,
            is_known=detection.is_known,
            camera_name="Camera"  # TODO: Get actual camera name
        )
        
        # GSM Fallback
        is_online = check_internet_connection()
        
        if not is_online:
            logger.warning("Internet is DOWN. Attempting GSM fallback...")
            
            try:
                from src.hardware.gsm_modem import get_modem
                modem = get_modem()
                
                if not modem.is_connected:
                    modem.connect()
                
                if modem.is_connected:
                    alert_type = "INTRUSION" if not detection.is_known else "VISITOR"
                    message = f"FacePro Alert: {alert_type} detected! Object: {detection.label or 'Unknown'}"
                    modem.send_sms(message)
                else:
                    logger.error("GSM Modem not connected, cannot send fallback SMS")
            except Exception as e:
                logger.error(f"GSM fallback failed: {e}")
    
    def _add_event(self, event_data: Dict):
        """Events siyahısına yeni element əlavə edir."""
        item = QListWidgetItem()
        widget = EventListItem(event_data)
        item.setSizeHint(widget.sizeHint())
        
        self.events_list.insertItem(0, item)
        self.events_list.setItemWidget(item, widget)
        
        # Maksimum 100 event saxla
        while self.events_list.count() > 100:
            self.events_list.takeItem(self.events_list.count() - 1)
    
    def _clear_events(self):
        """Events siyahısını təmizləyir."""
        self.events_list.clear()
    
    def _log_event_to_db(self, event_type: str, object_label: str, confidence: float, snapshot_path: Optional[str]):
        """Hadisəni database-ə yazır."""
        try:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'db', 'faceguard.db'
            )
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO events (event_type, object_label, confidence, snapshot_path, created_at)
                VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
            """, (event_type, object_label, confidence, snapshot_path))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log event to DB: {e}")

    def _export_events(self):
        """Events-i fayla export edir (CSV/JSON)."""
        # Fayl seçimi
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Events", "",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if not path:
            return
            
        try:
            # DB-dən oxu
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'db', 'faceguard.db'
            )
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Dict kimi oxumaq üçün
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM events ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            events = [dict(row) for row in rows]
            conn.close()
            
            if not events:
                QMessageBox.information(self, "Export", "No events to export.")
                return
            
            # Export logic
            if path.endswith('.csv'):
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=events[0].keys())
                    writer.writeheader()
                    writer.writerows(events)
            elif path.endswith('.json'):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(events, f, indent=4, ensure_ascii=False)
            
            QMessageBox.information(self, "Success", f"Successfully exported {len(events)} events.")
            logger.info(f"Events exported to {path}")
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
    
    def _show_settings(self):
        """Ayarlar dialoqunu göstərir."""
        dialog = SettingsDialog(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()
    
    def _on_settings_saved(self):
        """Ayarlar saxlanıldıqda."""
        self._config = load_config()
        
        # Telegram credentials yenilə
        telegram_config = self._config.get('telegram', {})
        self._telegram_notifier.update_credentials(
            bot_token=telegram_config.get('bot_token', ''),
            chat_id=telegram_config.get('chat_id', '')
        )
        
        # Status indicator yenilə
        if self._telegram_notifier.is_enabled:
            self.status_panel.telegram_indicator.set_status('online')
        else:
            self.status_panel.telegram_indicator.set_status('offline')
        
        logger.info("Settings reloaded")
    
    def _add_known_face(self):
        """Yeni tanınmış üz əlavə edir."""
        dialog = FaceEnrollmentDialog(self)
        dialog.face_enrolled.connect(self._on_face_enrolled)
        dialog.exec()
    
    def _manage_faces(self):
        """Üzləri idarə etmək dialoqunu göstərir."""
        dialog = ManageFacesDialog(self)
        dialog.exec()
    
    def _on_face_enrolled(self, name: str, image_path: str):
        """Yeni üz əlavə edildikdə."""
        logger.info(f"Face enrolled: {name} -> {image_path}")
        # AI worker-ə yeni üzü əlavə et
        if self._ai_worker:
            try:
                import cv2
                face_image = cv2.imread(image_path)
                if face_image is not None:
                    self._ai_worker.add_known_face(name, face_image)
            except Exception as e:
                logger.error(f"Failed to add face to AI worker: {e}")
    
    def _show_about(self):
        """About dialoqunu göstərir."""
        QMessageBox.about(
            self, 
            "About FacePro",
            """<h2>FacePro v1.0</h2>
            <p>Smart Security System with Face Recognition & Re-ID</p>
            <p>© 2025 NurMurDev</p>
            """
        )
    
    def closeEvent(self, event):
        """Pəncərə bağlanarkən."""
        if self._is_running:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "System is running. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self._stop_system()
        
        event.accept()


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
