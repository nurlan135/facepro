"""
FacePro Settings - Notifications Tab
Telegram və GSM bildiriş ayarları.
"""

from typing import Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QSpinBox, QCheckBox, QComboBox, QMessageBox
)

from src.hardware.gsm_modem import GSMModem
from src.hardware.telegram_notifier import TelegramNotifier


class NotificationsTab(QWidget):
    """Notifications settings tab."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Telegram
        telegram_group = QGroupBox("Telegram Bot")
        telegram_layout = QFormLayout(telegram_group)
        
        self.telegram_token_edit = QLineEdit()
        self.telegram_token_edit.setPlaceholderText("Bot token from @BotFather")
        self.telegram_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        telegram_layout.addRow("Bot Token:", self.telegram_token_edit)
        
        self.telegram_chat_edit = QLineEdit()
        self.telegram_chat_edit.setPlaceholderText("Chat ID")
        telegram_layout.addRow("Chat ID:", self.telegram_chat_edit)
        
        test_telegram_btn = QPushButton("Test Connection")
        test_telegram_btn.setProperty("class", "secondary")
        test_telegram_btn.clicked.connect(self._test_telegram)
        telegram_layout.addRow("", test_telegram_btn)
        
        layout.addWidget(telegram_group)
        
        # Telegram Notification Settings
        notif_group = QGroupBox("Bildiriş Ayarları")
        notif_layout = QFormLayout(notif_group)
        
        self.telegram_enabled_check = QCheckBox("Telegram bildirişlərini aktiv et")
        notif_layout.addRow("", self.telegram_enabled_check)
        
        self.notify_known_check = QCheckBox("Tanınmış şəxslər üçün də bildiriş göndər")
        self.notify_known_check.setToolTip("Söndürülübsə, yalnız naməlum şəxslər üçün bildiriş gəlir")
        notif_layout.addRow("", self.notify_known_check)
        
        self.notification_interval_spin = QSpinBox()
        self.notification_interval_spin.setRange(5, 300)
        self.notification_interval_spin.setSuffix(" saniyə")
        self.notification_interval_spin.setValue(30)
        self.notification_interval_spin.setToolTip("Eyni şəxs üçün bildiriş arası minimum fasilə")
        notif_layout.addRow("Bildiriş intervalı:", self.notification_interval_spin)
        
        layout.addWidget(notif_group)
        
        # GSM
        gsm_group = QGroupBox("GSM Modem (Offline SMS)")
        gsm_layout = QFormLayout(gsm_group)
        
        self.gsm_enabled_check = QCheckBox("Enable GSM Fallback")
        gsm_layout.addRow("", self.gsm_enabled_check)
        
        self.gsm_port_combo = QComboBox()
        self.gsm_port_combo.addItems(["COM1", "COM2", "COM3", "COM4"])
        
        refresh_ports_btn = QPushButton("Refresh")
        refresh_ports_btn.setFixedWidth(80)
        refresh_ports_btn.clicked.connect(self._refresh_com_ports)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(self.gsm_port_combo)
        port_layout.addWidget(refresh_ports_btn)
        gsm_layout.addRow("COM Port:", port_layout)
        
        self.gsm_phone_edit = QLineEdit()
        self.gsm_phone_edit.setPlaceholderText("+994501234567")
        gsm_layout.addRow("Phone Number:", self.gsm_phone_edit)
        
        test_gsm_btn = QPushButton("Test SMS")
        test_gsm_btn.setProperty("class", "secondary")
        gsm_layout.addRow("", test_gsm_btn)
        
        layout.addWidget(gsm_group)
        layout.addStretch()
    
    def load_settings(self, config: Dict[str, Any]):
        """Ayarları yükləyir."""
        # Telegram
        telegram_config = config.get('telegram', {})
        self.telegram_token_edit.setText(telegram_config.get('bot_token', ''))
        self.telegram_chat_edit.setText(telegram_config.get('chat_id', ''))
        self.telegram_enabled_check.setChecked(telegram_config.get('enabled', True))
        self.notify_known_check.setChecked(telegram_config.get('notify_known_persons', False))
        self.notification_interval_spin.setValue(telegram_config.get('notification_interval', 30))
        
        # GSM
        gsm_config = config.get('gsm', {})
        self.gsm_enabled_check.setChecked(gsm_config.get('enabled', False))
        self.gsm_phone_edit.setText(gsm_config.get('phone_number', ''))
        
        # COM ports
        self._refresh_com_ports()
    
    def get_settings(self) -> Dict[str, Any]:
        """Ayarları qaytarır."""
        com_port_text = self.gsm_port_combo.currentText()
        if com_port_text and ' ' in com_port_text:
            com_port = com_port_text.split()[0]
        elif com_port_text:
            com_port = com_port_text
        else:
            com_port = 'COM3'
        
        return {
            'telegram': {
                'bot_token': self.telegram_token_edit.text(),
                'chat_id': self.telegram_chat_edit.text()
            },
            'gsm': {
                'enabled': self.gsm_enabled_check.isChecked(),
                'com_port': self.gsm_port_combo.currentData() or com_port,
                'baud_rate': 9600,
                'phone_number': self.gsm_phone_edit.text()
            }
        }
    
    def _refresh_com_ports(self):
        """COM portlarını yeniləyir."""
        ports = GSMModem.list_available_ports()
        self.gsm_port_combo.clear()
        for port in ports:
            self.gsm_port_combo.addItem(f"{port['port']} - {port['description']}", port['port'])
    
    def _test_telegram(self):
        """Telegram bağlantısını test edir."""
        token = self.telegram_token_edit.text().strip()
        chat_id = self.telegram_chat_edit.text().strip()
        
        if not token or not chat_id:
            QMessageBox.warning(
                self, "Error",
                "Please enter both Bot Token and Chat ID."
            )
            return
        
        notifier = TelegramNotifier(bot_token=token, chat_id=chat_id)
        success, message = notifier.test_connection()
        notifier.stop()
        
        if success:
            QMessageBox.information(
                self, "Success",
                f"✅ {message}\n\nTest mesajı Telegram-a göndərildi!"
            )
        else:
            QMessageBox.critical(
                self, "Error",
                f"❌ {message}"
            )
