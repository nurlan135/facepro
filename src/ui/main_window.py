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
import sqlite3
import csv
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.i18n import tr, get_translator
from src.utils.helpers import (
    load_config, load_cameras, save_snapshot, 
    get_timestamp, get_db_path, save_event
)
from src.ui.styles import DARK_THEME, COLORS
from src.ui.settings_dialog import SettingsDialog
from src.ui.face_enrollment import FaceEnrollmentDialog, ManageFacesDialog
from src.core.camera_thread import CameraConfig, CameraManager
from src.core.ai_thread import AIWorker, FrameResult, Detection, DetectionType, draw_detections
from src.core.cleaner import get_cleaner
from src.hardware.telegram_notifier import get_telegram_notifier

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
        self._telegram_notifier = get_telegram_notifier()
        self._auth_manager = get_auth_manager()
        
        # State
        self._is_running = False
        self._known_faces_count = 0 
        self._total_detections_count = 0
        
        self.setWindowTitle("FacePro - Smart Security System")
        self.resize(1366, 768)
        self.setStyleSheet(DARK_THEME)
        
        self._setup_ui()
        self._setup_tray()
        self._setup_auth_integration()
        
        # Connect language change signal
        get_translator().language_changed.connect(self._on_language_changed)
        
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
        self.camera_page.toggle_system_clicked.connect(self._toggle_running)
        self.pages.addWidget(self.camera_page)
        
        # Page 2: Logs View
        self.logs_page = LogsPage()
        self.logs_page.export_clicked.connect(self._export_events)
        self.pages.addWidget(self.logs_page)
        
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

    def _start_system(self):
        """Sistemi başladır."""
        if not self._cameras_config:
            QMessageBox.warning(self, tr('msg_error'), "No cameras configured!")
            return
        
        # Setup cameras
        for cam_cfg in self._cameras_config:
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
        
        # Add to activity feed
        item = QListWidgetItem()
        widget = ActivityItem(detection.label, time_str, is_known, camera_name)
        item.setSizeHint(widget.sizeHint())
        self.home_page.activity_feed.insertItem(0, item)
        self.home_page.activity_feed.setItemWidget(item, widget)
        
        # Limit items
        if self.home_page.activity_feed.count() > 20:
            self.home_page.activity_feed.takeItem(self.home_page.activity_feed.count() - 1)
        
        # Also add to logs
        log_item = QListWidgetItem()
        log_widget = ActivityItem(detection.label, time_str, is_known, camera_name)
        log_item.setSizeHint(log_widget.sizeHint())
        self.logs_page.logs_list.insertItem(0, log_item)
        self.logs_page.logs_list.setItemWidget(log_item, log_widget)
        
        # Update log count
        self.logs_page.update_count(self.logs_page.logs_list.count())
        
        # Save event to database
        event_type = detection.type.value if hasattr(detection.type, 'value') else str(detection.type)
        identification_method = getattr(detection, 'identification_method', 'unknown') or 'unknown'
        save_event(
            event_type=event_type,
            object_label=detection.label,
            confidence=detection.confidence,
            snapshot_path=None,  # Snapshot saved separately if needed
            identification_method=identification_method
        )
        
        self._update_stats()

    def _update_stats(self):
        """Stats widget-i yenilə."""
        try:
            db_path = get_db_path()
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT Count(*) FROM users")
                self._known_faces_count = cursor.fetchone()[0]
                conn.close()
        except:
            pass
        
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
            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 1000")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            conn.close()
            
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
