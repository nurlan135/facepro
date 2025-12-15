
"""
FacePro Internationalization Module
Multilanguage support (AZ, EN, RU).
"""

from typing import Dict, Any, Optional
from .helpers import load_config

# Translation Dictionary
TRANSLATIONS = {
    "en": {
        # Menu
        "menu_file": "File",
        "menu_view": "View",
        "menu_tools": "Tools", 
        "menu_help": "Help",
        "action_exit": "Exit",
        "action_faces_add": "Add Known Face",
        "action_faces_manage": "Manage Faces",
        "action_export_events": "Export Events",
        "action_license_info": "License Info",
        
        # Main Window
        "status_system": "System Status",
        "status_cpu": "CPU Usage",
        "status_ram": "RAM Usage",
        "status_disk": "Disk Usage",
        "status_net": "Internet",
        "status_gsm": "GSM Modem",
        "status_telegram": "Telegram",
        "last_events": "Last Events",
        "camera_feed": "Camera Feed",
        "events_clear": "Clear",
        "events_export": "Export",
        
        # Settings
        "settings_title": "Settings",
        "tab_general": "General",
        "tab_camera": "Camera",
        "tab_ai": "AI & Detection",
        "tab_storage": "Storage",
        "tab_notifications": "Notifications",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "lbl_language": "Language",
        "lbl_theme": "Theme",
        "lbl_app_name": "Application Name",
        
        # Camera
        "lbl_rtsp_url": "RTSP URL",
        "lbl_webcam_id": "Webcam ID",
        "btn_test_camera": "Test Camera",
        
        # AI
        "lbl_motion_sensitive": "Motion Sensitivity",
        "lbl_face_conf": "Face Confidence",
        "lbl_classes": "Objects to Detect",
        
        # Notifications
        "lbl_telegram_token": "Bot Token",
        "lbl_chat_id": "Chat ID",
        "btn_test_conn": "Test Connection",
        "lbl_gsm_port": "COM Port",
        "lbl_gsm_phone": "Phone Number",
        
        # Messages
        "msg_restart_required": "Restart Required",
        "msg_restart_detail": "Please restart the application to apply language changes.",
        "msg_saved": "Settings saved successfully.",
        "msg_error": "Error",
        "msg_success": "Success"
    },
    
    "az": {
        # Menu
        "menu_file": "Fayl",
        "menu_view": "Görünüş",
        "menu_tools": "Alətlər",
        "menu_help": "Kömək",
        "action_exit": "Çıxış",
        "action_faces_add": "Tanınmış Üz Əlavə Et",
        "action_faces_manage": "Üzləri İdarə Et",
        "action_export_events": "Hadisələri İxrac Et",
        "action_license_info": "Lisenziya Məlumatı",
        
        # Main Window
        "status_system": "Sistem Statusu",
        "status_cpu": "CPU İstifadəsi",
        "status_ram": "RAM İstifadəsi",
        "status_disk": "Disk İstifadəsi",
        "status_net": "İnternet",
        "status_gsm": "GSM Modem",
        "status_telegram": "Telegram",
        "last_events": "Son Hadisələr",
        "camera_feed": "Kamera Görüntüsü",
        "events_clear": "Təmizlə",
        "events_export": "İxrac",
        
        # Settings
        "settings_title": "Ayarlar",
        "tab_general": "Ümumi",
        "tab_camera": "Kamera",
        "tab_ai": "AI & Aşkarlama",
        "tab_storage": "Yaddaş",
        "tab_notifications": "Bildirişlər",
        "btn_save": "Yadda Saxla",
        "btn_cancel": "Ləğv Et",
        "lbl_language": "Dil",
        "lbl_theme": "Mövzu",
        "lbl_app_name": "Tətbiq Adı",
        
        # Camera
        "lbl_rtsp_url": "RTSP URL",
        "lbl_webcam_id": "Webcam ID",
        "btn_test_camera": "Kameranı Yoxla",
        
        # AI
        "lbl_motion_sensitive": "Hərəkət Həssaslığı",
        "lbl_face_conf": "Üz Tanıma Dəqiqliyi",
        "lbl_classes": "Aşkarlanan Obyektlər",
        
        # Notifications
        "lbl_telegram_token": "Bot Token",
        "lbl_chat_id": "Chat ID",
        "btn_test_conn": "Əlaqəni Yoxla",
        "lbl_gsm_port": "COM Port",
        "lbl_gsm_phone": "Telefon Nömrəsi",
        
        # Messages
        "msg_restart_required": "Yenidən Başlatma",
        "msg_restart_detail": "Dili dəyişmək üçün tətbiqi yenidən başladın.",
        "msg_saved": "Ayarlar uğurla yadda saxlanıldı.",
        "msg_error": "Səhv",
        "msg_success": "Uğurlu"
    },
    
    "ru": {
        # Menu
        "menu_file": "Файл",
        "menu_view": "Вид",
        "menu_tools": "Инструменты",
        "menu_help": "Помощь",
        "action_exit": "Выход",
        "action_faces_add": "Добавить Лицо",
        "action_faces_manage": "Управление Лицами",
        "action_export_events": "Экспорт Событий",
        "action_license_info": "Лицензия",
        
        # Main Window
        "status_system": "Состояние Системы",
        "status_cpu": "Загрузка CPU",
        "status_ram": "Загрузка RAM",
        "status_disk": "Диск",
        "status_net": "Интернет",
        "status_gsm": "GSM Модем",
        "status_telegram": "Telegram",
        "last_events": "Последние События",
        "camera_feed": "Камеры",
        "events_clear": "Очистить",
        "events_export": "Экспорт",
        
        # Settings
        "settings_title": "Настройки",
        "tab_general": "Общие",
        "tab_camera": "Камера",
        "tab_ai": "ИИ и Детекция",
        "tab_storage": "Хранилище",
        "tab_notifications": "Уведомления",
        "btn_save": "Сохранить",
        "btn_cancel": "Отмена",
        "lbl_language": "Язык",
        "lbl_theme": "Тема",
        "lbl_app_name": "Название приложения",
        
        # Camera
        "lbl_rtsp_url": "RTSP URL",
        "lbl_webcam_id": "ID Веб-камеры",
        "btn_test_camera": "Проверить Камеру",
        
        # AI
        "lbl_motion_sensitive": "Чувств. Движения",
        "lbl_face_conf": "Точность (Лица)",
        "lbl_classes": "Объекты",
        
        # Notifications
        "lbl_telegram_token": "Bot Token",
        "lbl_chat_id": "Chat ID",
        "btn_test_conn": "Проверить",
        "lbl_gsm_port": "COM Порт",
        "lbl_gsm_phone": "Номер Телефона",
        
        # Messages
        "msg_restart_required": "Требуется Перезапуск",
        "msg_restart_detail": "Пожалуйста, перезапустите приложение для смены языка.",
        "msg_saved": "Настройки сохранены.",
        "msg_error": "Ошибка",
        "msg_success": "Успешно"
    }
}

class Translator:
    def __init__(self):
        self._language = "en"
        self._load_language()
        
    def _load_language(self):
        config = load_config()
        self._language = config.get("ui", {}).get("language", "en")
        
    def tr(self, key: str) -> str:
        """
        Açar sözə uyğun tərcüməni qaytarır.
        Məs: tr("menu_file")
        """
        lang_dict = TRANSLATIONS.get(self._language, TRANSLATIONS["en"])
        return lang_dict.get(key, key)
    
    @property
    def current_language(self) -> str:
        return self._language

# Global instance
_translator = Translator()

def tr(key: str) -> str:
    """Qlobal tərcümə funksiyası."""
    return _translator.tr(key)
