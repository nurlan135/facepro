"""
FacePro Backup & Restore Dialog
UI for creating and managing backups.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QTableWidget, QTableWidgetItem, QMessageBox, 
    QHeaderView, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread

from src.utils.backup_manager import BackupManager
from src.utils.logger import get_logger
from src.utils.i18n import tr

logger = get_logger()

class BackupWorker(QThread):
    """Worker thread for backup/restore operations to keep UI responsive"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, manager: BackupManager, task: str, **kwargs):
        super().__init__()
        self.manager = manager
        self.task = task
        self.kwargs = kwargs
        
    def run(self):
        try:
            if self.task == 'create':
                success, result = self.manager.create_backup(
                    self.kwargs.get('db', True),
                    self.kwargs.get('faces', True),
                    self.kwargs.get('settings', True)
                )
                if success:
                    from src.utils.audit_logger import get_audit_logger
                    get_audit_logger().log("BACKUP_CREATED", {"path": result})
                self.finished.emit(success, result)
            elif self.task == 'restore':
                success, result = self.manager.restore_backup(
                    self.kwargs.get('path'),
                    self.kwargs.get('db', True),
                    self.kwargs.get('faces', True),
                    self.kwargs.get('settings', True)
                )
                if success:
                    from src.utils.audit_logger import get_audit_logger
                    get_audit_logger().log("DATABASE_RESTORED", {"path": self.kwargs.get('path')})
                self.finished.emit(success, result)
        except Exception as e:
            self.finished.emit(False, str(e))

class BackupDialog(QDialog):
    """Backup management dialog UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = BackupManager()
        self.worker = None
        self._setup_ui()
        self._refresh_backups()
        
    def _setup_ui(self):
        self.setWindowTitle(tr('backup_title') if tr('backup_title') != 'backup_title' else "Backup & Restore")
        self.setMinimumSize(600, 450)
        
        layout = QVBoxLayout(self)
        
        # Upper section: Create backup
        create_group = QVBoxLayout()
        create_group.addWidget(QLabel(f"<b>{tr('create_backup') if tr('create_backup') != 'create_backup' else 'Yeni Backup Yarat'}</b>"))
        
        cb_layout = QHBoxLayout()
        self.cb_db = QCheckBox(tr('backup_db') if tr('backup_db') != 'backup_db' else "Verilənlər bazası")
        self.cb_db.setChecked(True)
        self.cb_faces = QCheckBox(tr('backup_faces') if tr('backup_faces') != 'backup_faces' else "Üz şəkilləri")
        self.cb_faces.setChecked(True)
        self.cb_settings = QCheckBox(tr('backup_settings') if tr('backup_settings') != 'backup_settings' else "Ayarlar")
        self.cb_settings.setChecked(True)
        
        cb_layout.addWidget(self.cb_db)
        cb_layout.addWidget(self.cb_faces)
        cb_layout.addWidget(self.cb_settings)
        create_group.addLayout(cb_layout)
        
        self.btn_create = QPushButton(tr('btn_create_backup') if tr('btn_create_backup') != 'btn_create_backup' else "Backup Yarat")
        self.btn_create.setProperty("class", "primary")
        self.btn_create.clicked.connect(self._on_create_clicked)
        create_group.addWidget(self.btn_create)
        
        layout.addLayout(create_group)
        layout.addSpacing(20)
        
        # Middle section: Backups list
        layout.addWidget(QLabel(f"<b>{tr('existing_backups') if tr('existing_backups') != 'existing_backups' else 'Mövcud Backuplar'}</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            tr('name') if tr('name') != 'name' else "Ad",
            tr('size') if tr('size') != 'size' else "Ölçü",
            tr('date') if tr('date') != 'date' else "Tarix"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)
        
        # Progress bar (hidden by default)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Infinite animation
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Bottom section: Actions
        btn_layout = QHBoxLayout()
        
        self.btn_restore = QPushButton(tr('btn_restore') if tr('btn_restore') != 'btn_restore' else "Geri Yüklə")
        self.btn_restore.clicked.connect(self._on_restore_clicked)
        
        self.btn_delete = QPushButton(tr('btn_delete') if tr('btn_delete') != 'btn_delete' else "Sil")
        self.btn_delete.setProperty("class", "danger")
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        
        self.btn_import = QPushButton(tr('btn_import') if tr('btn_import') != 'btn_import' else "İmport...")
        self.btn_import.clicked.connect(self._on_import_clicked)
        
        btn_layout.addWidget(self.btn_restore)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_import)
        
        layout.addLayout(btn_layout)
        
    def _refresh_backups(self):
        backups = self.manager.list_backups()
        self.table.setRowCount(len(backups))
        
        for i, b in enumerate(backups):
            self.table.setItem(i, 0, QTableWidgetItem(b['name']))
            self.table.setItem(i, 1, QTableWidgetItem(f"{b['size_mb']} MB"))
            self.table.setItem(i, 2, QTableWidgetItem(b['created_at']))
            
    def _on_create_clicked(self):
        self._set_busy(True)
        self.worker = BackupWorker(
            self.manager, 'create',
            db=self.cb_db.isChecked(),
            faces=self.cb_faces.isChecked(),
            settings=self.cb_settings.isChecked()
        )
        self.worker.finished.connect(self._on_task_finished)
        self.worker.start()
        
    def _on_restore_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Xəta", "Zəhmət olmasa backup seçin.")
            return
            
        name = self.table.item(row, 0).text()
        path = [b['path'] for b in self.manager.list_backups() if b['name'] == name][0]
        
        reply = QMessageBox.question(
            self, "Təsdiq", 
            f"Diqqət! Bu əməliyyat cari məlumatların üzərinə yazacaq.\n'{name}' geri yüklənsin?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._set_busy(True)
            self.worker = BackupWorker(
                self.manager, 'restore',
                path=path,
                db=self.cb_db.isChecked(),
                faces=self.cb_faces.isChecked(),
                settings=self.cb_settings.isChecked()
            )
            self.worker.finished.connect(self._on_task_finished)
            self.worker.start()
            
    def _on_delete_clicked(self):
        row = self.table.currentRow()
        if row < 0: return
        
        name = self.table.item(row, 0).text()
        if QMessageBox.question(self, "Təsdiq", f"'{name}' silinsin?") == QMessageBox.StandardButton.Yes:
            if self.manager.delete_backup(name):
                self._refresh_backups()
                
    def _on_import_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Backup seçin", "", "ZIP faylları (*.zip)")
        if path:
            import shutil
            dest = os.path.join(self.manager.backup_dir, os.path.basename(path))
            shutil.copy2(path, dest)
            self._refresh_backups()
            
    def _on_task_finished(self, success: bool, result: str):
        self._set_busy(False)
        if success:
            QMessageBox.information(self, "Uğurlu", "Əməliyyat tamamlandı.")
            self._refresh_backups()
        else:
            QMessageBox.critical(self, "Xəta", f"Əməliyyat uğursuz oldu:\n{result}")
            
    def _set_busy(self, busy: bool):
        self.btn_create.setEnabled(not busy)
        self.btn_restore.setEnabled(not busy)
        self.btn_import.setEnabled(not busy)
        self.progress.setVisible(busy)
