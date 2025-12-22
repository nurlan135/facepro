"""
FacePro Main Window Module
Əsas Dashboard UI pəncərəsi - Refactored.
"""

from typing import Optional, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidgetItem,
    QMessageBox, QFileDialog, QSystemTrayIcon, QStyle, QApplication,
    QStackedWidget, QTabWidget, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

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

from src.core.database.repositories.event_repository import EventRepository
from src.core.database.repositories.user_repository import UserRepository

import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.i18n import tr, get_translator
from src.utils.helpers import (
    load_config, load_cameras, save_snapshot, 
    get_timestamp, get_db_path
)
from src.ui.styles import DARK_THEME, COLORS
from src.ui.settings_dialog import SettingsDialog
from src.ui.face_enrollment import FaceEnrollmentDialog, ManageFacesDialog
from src.core.camera_thread import CameraConfig, CameraManager
from src.core.ai_thread import AIWorker, FrameResult, Detection, DetectionType, draw_detections
from src.core.cleaner import get_cleaner
from src.hardware.telegram_notifier import get_telegram_notifier
from src.core.storage_worker import StorageWorker
from src.core.workers.data_loader import DataLoaderWorker

# Dashboard components
from src.ui.dashboard import SidebarWidget, HomePage, CameraPage, LogsPage, ActivityItem

# Auth components
from src.utils.auth_manager import get_auth_manager
from src.ui.user_management import UserManagementDialog
from src.ui.change_password import ChangePasswordDialog

logger = get_logger()


class MainWindow(QMainWindow):
    """Əsas tətbiq pəncərəsi - Dashboard Design (Refactored)."""
    
    def __init__(self):
        super().__init__()
        
        self._config = load_config()
        self._cameras_config = load_cameras()
        
        # Managers
        self._camera_manager = CameraManager()
        self._ai_worker: Optional[AIWorker] = None
        self._storage_worker: Optional[StorageWorker] = StorageWorker()
        self._data_loader = DataLoaderWorker()
        self._telegram_notifier = get_telegram_notifier()
        self._auth_manager = get_auth_manager()
        
        # Repositories
        self._event_repo = EventRepository()
        self._user_repo = UserRepository()
        
        # State
        self._is_running = False
        self._known_faces_count = 0 
        self._total_detections_count = 0
        self._selected_camera_name = None  # Seçilmiş kamera adı
        self._logs_offset = 0
        
        self.setWindowTitle("FacePro - Smart Security System")
        self.resize(1366, 768)
        self.setStyleSheet(DARK_THEME)
        
        self._setup_ui()
        self._setup_tray()
        self._setup_auth_integration()
        
        # Connect language change signal
        get_translator().language_changed.connect(self._on_language_changed)
        
        # Connect data loader signals
        self._data_loader.events_loaded.connect(self._on_events_loaded)
        self._data_loader.error_occurred.connect(self._on_data_error)
        
        # Initial Data Load for stats
        self._update_stats()
        
        # Apply role-based UI restrictions
        self._apply_role_based_ui()
        
        logger.info("MainWindow initialized (Dashboard Design)")

    def _setup_ui(self):
        """UI setup - Dashboard Layout."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.manage_faces_clicked.connect(self._manage_faces)
        self.sidebar.settings_clicked.connect(self._show_settings)
        self.sidebar.user_management_clicked.connect(self._show_user_management)
        self.sidebar.change_password_clicked.connect(self._show_change_password)
        self.sidebar.logout_clicked.connect(self._logout)
        self.sidebar.exit_clicked.connect(self._quit_application)
        main_layout.addWidget(self.sidebar)
        
        # Main Content Area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Top Navigation (Tabs centered)
        top_nav_layout = QHBoxLayout()
        top_nav_layout.addStretch()
        
        self.nav_tabs = QTabWidget()
        self.nav_tabs.addTab(QWidget(), tr('tab_home'))
        self.nav_tabs.addTab(QWidget(), tr('tab_camera'))
        self.nav_tabs.addTab(QWidget(), tr('tab_logs'))
        self.nav_tabs.setFixedHeight(50)
        self.nav_tabs.currentChanged.connect(self._on_tab_changed)
        
        top_nav_layout.addWidget(self.nav_tabs)
        top_nav_layout.addStretch()
        content_layout.addLayout(top_nav_layout)
        
        # Stacked Pages
        self.pages = QStackedWidget()
        
        # Page 0: Dashboard Home
        self.home_page = HomePage()
        self.home_page.start_camera_clicked.connect(self._toggle_running_from_card)
        self.home_page.add_face_clicked.connect(self._add_known_face)
        self.home_page.view_logs_clicked.connect(lambda: self.nav_tabs.setCurrentIndex(2))
        self.pages.addWidget(self.home_page)
        
        # Page 1: Camera View
        self.camera_page = CameraPage()
        self.camera_page.select_camera_clicked.connect(self._show_camera_selector)
        self.camera_page.start_clicked.connect(self._start_system)
        self.camera_page.stop_clicked.connect(self._stop_system)
        self.pages.addWidget(self.camera_page)
        
        # Page 2: Logs View
        self.logs_page = LogsPage()
        self.logs_page.export_clicked.connect(self._export_events)
        self.logs_page.load_more_clicked.connect(self._on_load_more_logs)
        self.pages.addWidget(self.logs_page)
        
        # Load initial events
        self._load_initial_events()
        
        content_layout.addWidget(self.pages)
        main_layout.addWidget(content_area)

    def _on_tab_changed(self, index):
        """Tab dəyişdikdə səhifəni dəyiş."""
        self.pages.setCurrentIndex(index)

    def _toggle_running_from_card(self):
        """Dashboard kartından sistemi başlat/dayandır."""
        self._toggle_running()
        if self._is_running:
            self.nav_tabs.setCurrentIndex(1)

    def _toggle_running(self):
        """Sistemi başlat/dayandır."""
        if self._is_running:
            self._stop_system()
        else:
            self._start_system()
    
    def _show_camera_selector(self):
        """Kamera seçim dialoqu (Mövcud kameraları göstər və ya yeni əlavə et)."""
        from src.ui.camera_dialogs.camera_selection_dialog import CameraSelectionDialog
        
        dialog = CameraSelectionDialog(self, self._cameras_config)
        
        # Connect signals
        dialog.camera_selected.connect(self._on_camera_selected)
        dialog.add_local_camera_requested.connect(self._on_add_local_camera)
        dialog.add_rtsp_camera_requested.connect(self._on_add_rtsp_camera)
        
        dialog.exec()

    def _on_camera_selected(self, name):
        """Mövcud kameranı seç."""
        self._selected_camera_name = name
        self.camera_page.set_camera_status(name)
        QMessageBox.information(
            self, 
            tr('camera_dialog.camera_selected'), 
            tr('camera_dialog.camera_selected_msg').replace('{name}', name)
        )
    
    def _on_add_local_camera(self):
        """Lokal kamera seçimi."""
        from src.ui.camera_dialogs import LocalCameraSelector
        
        dialog = LocalCameraSelector(parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            camera_data = dialog.get_camera_data()
            if camera_data:
                self._cameras_config.append(camera_data)
                self.camera_page.set_camera_status(camera_data.get('name', ''))
    
    def _on_add_rtsp_camera(self):
        """RTSP kamera seçimi."""
        from src.ui.camera_dialogs import RTSPConfigDialog
        
        dialog = RTSPConfigDialog(parent=self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            camera_data = dialog.get_camera_data()
            if camera_data:
                self._cameras_config.append(camera_data)
                self.camera_page.set_camera_status(camera_data.get('name', ''))

    def _start_system(self):
        """Sistemi başladır."""
        if not self._cameras_config:
            QMessageBox.warning(self, tr('msg_error'), tr('camera_dialog.no_cameras_configured'))
            return
        
        # Hansi kameraları başlatmaq lazımdır?
        if self._selected_camera_name:
            # Yalnız seçilmiş kameranı başlat
            cameras_to_start = [c for c in self._cameras_config if c['name'] == self._selected_camera_name]
        else:
            # Hamısını başlat
            cameras_to_start = self._cameras_config
        
        if not cameras_to_start:
            QMessageBox.warning(self, tr('msg_error'), tr('camera_dialog.no_camera_selected_msg'))
            return
        
        # Setup cameras
        for cam_cfg in cameras_to_start:
            config = CameraConfig(
                name=cam_cfg['name'],
                source=cam_cfg['source'],
                roi_points=cam_cfg.get('roi_points', [])
            )
            worker = self._camera_manager.add_camera(config)
            self.camera_page.video_grid.add_camera_view(config.name)
            
            # Connect signals from each worker
            worker.frame_ready.connect(self._on_camera_frame)
            worker.connection_status.connect(self._on_camera_status)
        
        # Start AI Worker
        self._ai_worker = AIWorker()
        self._ai_worker.frame_processed.connect(self._on_frame_processed)
        self._ai_worker.detection_alert.connect(self._on_detection_alert)
        self._ai_worker.start()
        
        # Start Storage Worker
        if self._storage_worker:
            self._storage_worker.start()
        
        # Start cameras
        self._camera_manager.start_all()
        
        self._is_running = True
        self.camera_page.set_running_state(True)
        
        # Update camera status label
        if self._cameras_config:
            camera_info = self._cameras_config[0].get('name', self._cameras_config[0].get('source', ''))
            self.camera_page.set_camera_status(camera_info)
        
        if self._telegram_notifier:
            self._telegram_notifier.send_startup_message()
        
        logger.info("System started")

    def _stop_system(self):
        """Sistemi dayandırır."""
        self._camera_manager.stop_all()
        
        if self._ai_worker:
            self._ai_worker.stop()
            self._ai_worker.wait(3000)
            self._ai_worker = None
            
        if self._storage_worker:
            self._storage_worker.stop()
            self._storage_worker.wait(1000)
        
        self.camera_page.video_grid.clear_all()
        
        self._is_running = False
        self.camera_page.set_running_state(False)
        self.camera_page.set_camera_status("")  # Reset status
        
        logger.info("System stopped")
        
        if self._telegram_notifier:
            self._telegram_notifier.send_shutdown_message()

    @pyqtSlot(object, str)
    def _on_camera_frame(self, frame, camera_name: str):
        if self._ai_worker:
            self._ai_worker.process_frame(frame, camera_name)
    
    @pyqtSlot(bool, str)
    def _on_camera_status(self, connected: bool, camera_name: str):
        widget = self.camera_page.video_grid.get_widget(camera_name)
        if widget:
            widget.set_connected(connected)

    @pyqtSlot(object)
    def _on_frame_processed(self, result):
        # Update performance stats
        self.sidebar.perf_monitor.update_fps()
        if hasattr(result, 'processing_time_ms'):
            self.sidebar.perf_monitor.update_ai_time(result.processing_time_ms)
            
        widget = self.camera_page.video_grid.get_widget(result.camera_name)
        if widget and result.frame is not None:
            display_frame = draw_detections(result.frame, result.detections)
            widget.update_frame(display_frame)

    @pyqtSlot(object, object)
    def _on_detection_alert(self, detection, frame=None):
        """Detection alert işlə."""
        now = datetime.now()
        
        # Duplicate prevention: same person within 2 seconds
        cache_key = f"{detection.label}_{detection.camera_name if hasattr(detection, 'camera_name') else ''}"
        last_time = getattr(self, '_last_detection_times', {}).get(cache_key)
        
        if not hasattr(self, '_last_detection_times'):
            self._last_detection_times = {}
        
        if last_time and (now - last_time).total_seconds() < 2:
            return  # Skip duplicate
        
        self._last_detection_times[cache_key] = now
        self._total_detections_count += 1
        
        is_known = detection.label not in ["Naməlum", "Unknown", "Naməlum Şəxs"]
        time_str = now.strftime("%d.%m %H:%M:%S")  # Date + Time
        camera_name = getattr(detection, 'camera_name', '')
        
        # Add to activity feed (Newest Top)
        self.home_page.activity_feed.prepend_event(detection.label, time_str, is_known, camera_name)
        
        # Limit items
        if self.home_page.activity_feed.count() > 20:
            self.home_page.activity_feed.takeItem(self.home_page.activity_feed.count() - 1)
        
        # Also add to logs (Newest Top)
        self.logs_page.logs_list.prepend_event(detection.label, time_str, is_known, camera_name)
        
        # Limit log items to prevent UI lag/memory bloat
        if self.logs_page.logs_list.count() > 200:
            self.logs_page.logs_list.takeItem(self.logs_page.logs_list.count() - 1)
        
        # Update log count
        self.logs_page.update_count(self.logs_page.logs_list.count())
        
        # Save event using async StorageWorker
        if self._storage_worker:
            self._storage_worker.add_task(detection, frame)
            # When new event is added, we should logically increase offset 
            # if we want 'Load More' to stay consistent. But since it's at top, 
            # it's tricky. For now, we just update UI.
            self._logs_offset += 1 

    def _load_initial_events(self):
        """Loads first 20 events from DB on startup (Async)."""
        logger.info("Requesting initial events...")
        self.logs_page.btn_load_more.setEnabled(False) # Disable until loaded
        self._data_loader.load_events(limit=20, offset=0, request_type="initial")

    def _on_load_more_logs(self):
        """Loads more logs from DB using offset (Async)."""
        logger.info(f"Requesting more logs (offset={self._logs_offset})...")
        self.logs_page.btn_load_more.setEnabled(False)
        self.logs_page.btn_load_more.setText(tr('dashboard.loading'))
        self._data_loader.load_events(limit=50, offset=self._logs_offset, request_type="more")

    @pyqtSlot(list, int, str)
    def _on_events_loaded(self, events, count, request_type):
        """Handle loaded events from worker."""
        try:
            # Reset button state
            self.logs_page.btn_load_more.setEnabled(True)
            self.logs_page.btn_load_more.setText(tr('dashboard.btn_load_more'))
            
            if not events:
                if request_type == "more":
                    self.logs_page.btn_load_more.setEnabled(False)
                    self.logs_page.btn_load_more.setText(tr('dashboard.no_more_records'))
                return

            if request_type == "initial":
                self._logs_offset = 0 # Reset offset
            
            processed_items = []
            
            for event in events:
                label = event[2] or "Unknown"
                time_str = event[6]
                is_known = label not in ["Naməlum", "Unknown", "Naməlum Şəxs"]
                camera_name = "" 
                processed_items.append((label, time_str, is_known, camera_name))

            if request_type == "initial":
                # Activity Feed (Home Page) - Newest Top
                # When using insert(0), iterating from reversed(events) [Old->New] -> Old, New -> Newest at Top.
                for label, time_str, is_known, cam_name in reversed(processed_items):
                    self.home_page.activity_feed.prepend_event(label, time_str, is_known, cam_name)

                # Logs Page (List) - Newest Top
                for label, time_str, is_known, cam_name in reversed(processed_items):
                    self.logs_page.logs_list.prepend_event(label, time_str, is_known, cam_name)

                self._logs_offset = len(events)
                logger.info(f"Async: Loaded {len(events)} initial events")

            elif request_type == "more":
                for label, time_str, is_known, cam_name in processed_items:
                    self.logs_page.logs_list.append_event(label, time_str, is_known, cam_name)
                
                self._logs_offset += len(events)
                logger.info(f"Async: Loaded {len(events)} more logs (Total: {self._logs_offset})")

            # Update count
            self.logs_page.update_count(self.logs_page.logs_list.count())
            
        except Exception as e:
            logger.error(f"Error handling loaded events: {e}")
        
        self._update_stats()

    @pyqtSlot(str)
    def _on_data_error(self, error_msg):
        self.logs_page.btn_load_more.setEnabled(True)
        self.logs_page.btn_load_more.setText(tr('dashboard.error_retry'))
        logger.error(f"Data Loader Error: {error_msg}")

    def _update_stats(self):
        """Stats widget-i yenilə."""
        try:
            self._known_faces_count = self._user_repo.get_user_count()
        except Exception:
            self._known_faces_count = 0
        
        self.sidebar.update_stats(self._known_faces_count, self._total_detections_count)

    def _manage_faces(self):
        """Manage faces dialog (Admin only)."""
        if not self._auth_manager.can_enroll_faces():
            QMessageBox.warning(self, "Access Denied", "You don't have permission to manage faces.")
            return
        
        dialog = ManageFacesDialog(self)
        dialog.exec()
        self._update_stats()

    def _add_known_face(self):
        """Add known face dialog (Admin only)."""
        if not self._auth_manager.can_enroll_faces():
            QMessageBox.warning(self, "Access Denied", "You don't have permission to enroll faces.")
            return
        
        dialog = FaceEnrollmentDialog(parent=self)
        if dialog.exec():
            self._update_stats()
            if self._ai_worker:
                self._ai_worker.reload_known_faces()

    def _show_settings(self):
        """Show settings dialog (Admin only)."""
        if not self._auth_manager.can_access_settings():
            QMessageBox.warning(self, "Access Denied", "You don't have permission to access settings.")
            return
        
        dialog = SettingsDialog(self)
        dialog.exec()
        self._config = load_config()
        self._cameras_config = load_cameras()
    
    def _show_user_management(self):
        """Show user management dialog (Admin only)."""
        if not self._auth_manager.can_manage_users():
            QMessageBox.warning(self, "Access Denied", "You don't have permission to manage users.")
            return
        
        dialog = UserManagementDialog(self)
        dialog.exec()
    
    def _show_change_password(self):
        """Show change password dialog (All users)."""
        current_user = self._auth_manager.get_current_user()
        if not current_user:
            QMessageBox.warning(self, "Error", "No user logged in.")
            return
        
        dialog = ChangePasswordDialog(current_user.user_id, self)
        dialog.exec()
    
    def _setup_auth_integration(self):
        """Setup authentication system integration."""
        # Connect auth manager signals
        self._auth_manager.logout_requested.connect(self._on_logout_requested)
        self._auth_manager.session_timeout.connect(self._on_session_timeout)
        
        # Setup session timeout timer (check every minute)
        self._session_timer = QTimer(self)
        self._session_timer.timeout.connect(self._check_session_timeout)
        self._session_timer.start(60000)  # Check every 60 seconds
        
        # Install event filter to track user activity
        QApplication.instance().installEventFilter(self)
    
    def _apply_role_based_ui(self):
        """Apply role-based UI restrictions based on current user."""
        current_user = self._auth_manager.get_current_user()
        if not current_user:
            return
        
        # Update sidebar with user info
        self.sidebar.set_user_info(current_user.username, current_user.role)
        
        logger.info(f"Applied role-based UI for user '{current_user.username}' ({current_user.role})")
    
    def _logout(self):
        """Handle manual logout."""
        reply = QMessageBox.question(
            self, tr("logout_confirm_title"), tr("logout_confirm_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._auth_manager.logout()
    
    @pyqtSlot()
    def _on_logout_requested(self):
        """Handle logout signal from auth manager."""
        logger.info("Logout requested - stopping system and closing window")
        
        # Stop camera system
        if self._is_running:
            self._stop_system()
        
        # Close the main window
        self.close()
        
        # Show login dialog again
        from src.ui.login_dialog import LoginDialog
        login_dialog = LoginDialog()
        result = login_dialog.exec()
        
        if result == login_dialog.DialogCode.Accepted:
            # Re-apply role-based UI for new user
            self._apply_role_based_ui()
            self.show()
        else:
            # User cancelled login, exit application
            QApplication.quit()
    
    @pyqtSlot()
    def _on_session_timeout(self):
        """Handle session timeout signal."""
        logger.info("Session timeout - auto logout triggered")
        QMessageBox.information(
            self, tr("session_timeout_title"), 
            tr("session_timeout_msg")
        )
    
    def _check_session_timeout(self):
        """Periodically check if session has timed out."""
        if self._auth_manager.is_logged_in():
            # This will emit session_timeout signal if expired
            self._auth_manager.check_session_timeout()
    
    def eventFilter(self, obj, event):
        """
        Event filter to track user activity and reset session timer.
        
        Tracks mouse and keyboard events to detect user activity.
        Requirements: 6.1 - Session timeout based on inactivity
        """
        from PyQt6.QtCore import QEvent
        
        # Track user activity events
        activity_events = [
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseMove,
            QEvent.Type.KeyPress,
            QEvent.Type.KeyRelease,
            QEvent.Type.Wheel
        ]
        
        if event.type() in activity_events:
            # Reset activity timer on user interaction
            self._auth_manager.reset_activity_timer()
        
        return super().eventFilter(obj, event)

    def _export_events(self):
        """Hadisələri CSV formatında ixrac edir."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Events", f"events_{get_timestamp()}.csv",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if not path:
            return
        
        try:
            columns, rows = self._event_repo.get_all_events_for_export(1000)
            
            if path.endswith('.json'):
                data = [dict(zip(columns, row)) for row in rows]
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            else:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(rows)
            
            QMessageBox.information(self, tr('msg_success'), f"Exported to {path}")
            logger.info(f"Events exported to {path}")
        except Exception as e:
            QMessageBox.critical(self, tr('msg_error'), str(e))

    def _setup_tray(self):
        """System tray setup."""
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        menu.addAction(show_action)
        menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._quit_application)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(
            lambda reason: self.showNormal() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )

    def _quit_application(self):
        # Stop system if running
        if self._is_running:
            reply = QMessageBox.question(
                self, "Exit", "System is running. Exit?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No: 
                return
            self._stop_system()
        
        # Stop telegram notifier thread
        if self._telegram_notifier:
            self._telegram_notifier.stop()
        
        # Disconnect logout signal to prevent login dialog from appearing
        try:
            self._auth_manager.logout_requested.disconnect(self._on_logout_requested)
        except:
            pass
        
        # Logout before exiting for security (won't trigger login dialog now)
        if self._auth_manager.is_logged_in():
            self._auth_manager.logout()
        
        # Force quit application
        QApplication.quit()

    def closeEvent(self, event):
        # Check if this is a logout-triggered close (should not minimize to tray)
        if not self._auth_manager.is_logged_in():
            # User logged out, accept the close
            if hasattr(self, '_session_timer'):
                self._session_timer.stop()
            event.accept()
            return
        
        if self.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "FacePro", "Running in background...", 
                QSystemTrayIcon.MessageIcon.Information, 2000
            )
    
    def _on_language_changed(self, lang_code: str):
        """Dil dəyişdikdə bütün UI elementlərini yeniləyir."""
        logger.info(f"Language changed to: {lang_code}")
        
        # Update Tabs
        self.nav_tabs.setTabText(0, tr('tab_home'))
        self.nav_tabs.setTabText(1, tr('tab_camera'))
        self.nav_tabs.setTabText(2, tr('tab_logs'))
        
        # Update components via their update_language methods
        self.sidebar.update_language()
        self.home_page.update_language()
        self.camera_page.update_language()
        self.logs_page.update_language()
        
        # Update Stats
        self._update_stats()
        
        # Show confirmation
        QMessageBox.information(self, tr('msg_success'), tr('msg_language_changed'))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
