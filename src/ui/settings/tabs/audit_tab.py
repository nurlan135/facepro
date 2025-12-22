"""
FacePro Settings - Audit Logs Tab (Admin Only)
Sistemdə baş verən inzibati və təhlükəsizlik hadisələrinin tarixçəsi.
"""

from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFrame
)
from PyQt6.QtCore import Qt

from src.utils.audit_logger import get_audit_logger
from src.utils.i18n import tr
from src.ui.styles import COLORS

class AuditTab(QWidget):
    """Audit logs viewer tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._audit_logger = get_audit_logger()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with Refresh button
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"<b>{tr('audit_logs_title') if tr('audit_logs_title') != 'audit_logs_title' else 'Audit Tarixçəsi'}</b>"))
        header_layout.addStretch()
        
        self.btn_refresh = QPushButton(f"🔄 {tr('refresh') if tr('refresh') != 'refresh' else 'Yenilə'}")
        self.btn_refresh.setProperty("class", "secondary")
        self.btn_refresh.clicked.connect(self._load_logs)
        header_layout.addWidget(self.btn_refresh)
        
        layout.addLayout(header_layout)
        
        # Logs Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            tr('audit_timestamp') if tr('audit_timestamp') != 'audit_timestamp' else "Tarix",
            tr('audit_user') if tr('audit_user') != 'audit_user' else "İstifadəçi",
            tr('audit_action') if tr('audit_action') != 'audit_action' else "Hərəkət",
            tr('audit_details') if tr('audit_details') != 'audit_details' else "Detallar"
        ])
        
        # Table styling
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        # Status footer
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(self.status_lbl)

    def load_settings(self, config: Dict[str, Any]):
        """Baxıldıqda logları yeniləyir."""
        self._load_logs()
    
    def _load_logs(self):
        """Audit logları bazadan yükləyir."""
        logs = self._audit_logger.get_logs(limit=200)
        self.table.setRowCount(len(logs))
        
        for i, log in enumerate(logs):
            # Timestamp
            self.table.setItem(i, 0, QTableWidgetItem(log['timestamp']))
            # Username
            user_item = QTableWidgetItem(log['username'])
            if log['username'] == 'System':
                user_item.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(i, 1, user_item)
            # Action
            action_item = QTableWidgetItem(log['action'])
            self._style_action_item(action_item, log['action'])
            self.table.setItem(i, 2, action_item)
            # Details
            details_str = str(log['details'])
            self.table.setItem(i, 3, QTableWidgetItem(details_str))
        
        self.status_lbl.setText(f"Cəmi {len(logs)} hadisə göstərilir.")

    def _style_action_item(self, item: QTableWidgetItem, action: str):
        """Action tipinə görə rəngləndirmə."""
        critical_actions = ['USER_DELETED', 'DATABASE_RESTORED', 'ENCODING_DELETED', 'PERSON_DELETED']
        success_actions = ['LOGIN', 'BACKUP_CREATED', 'FACE_ENROLLED', 'USER_CREATED']
        
        if action in critical_actions:
            item.setForeground(Qt.GlobalColor.red)
        elif action in success_actions:
            item.setForeground(Qt.GlobalColor.green)

    def get_settings(self) -> Dict[str, Any]:
        """Audit tab ayarları qaytarmır (ancaq oxumaq üçündür)."""
        return {}
