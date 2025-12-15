
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal
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
        
        # Main Window / Dashboard
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
        
        # Dashboard Tabs & Sidebar
        "tab_home": "Home",
        "tab_camera": "Camera",
        "tab_logs": "Logs",
        "sidebar_admin": "Admin User",
        "sidebar_active": "Active",
        "sidebar_manage_faces": "Manage Faces",
        "sidebar_settings": "Profile & Settings",
        "sidebar_statistics": "Statistics",
        "sidebar_registered_faces": "Registered Faces",
        "sidebar_total_detections": "Total Detections",
        "sidebar_exit": "Exit",
        
        # Dashboard Cards
        "card_start_camera": "Start Camera",
        "card_start_camera_desc": "Activate face recognition system",
        "card_add_face": "Add Face",
        "card_add_face_desc": "Register a new person",
        "card_view_logs": "View Logs",
        "card_view_logs_desc": "Review event history",
        "card_stop_system": "Stop System",
        
        # Dashboard Other
        "welcome_title": "Welcome, Admin",
        "welcome_subtitle": "Your security is guaranteed with FacePro",
        "recent_activity": "Recent Activity",
        "logs_title": "System Logs & Events",
        "export_csv": "Export (CSV)",
        "start_system": "Start System",
        "filter_all": "All",
        "filter_known": "Known",
        "filter_unknown": "Unknown",
        "logs_entries": "entries",
        
        # Settings
        "settings_title": "Settings",
        "tab_general": "General",
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
        "msg_success": "Success",
        "msg_language_changed": "Language changed successfully!"
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
        
        # Main Window / Dashboard
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
        
        # Dashboard Tabs & Sidebar
        "tab_home": "Əsas Səhifə",
        "tab_camera": "Kamera",
        "tab_logs": "Jurnallar",
        "sidebar_admin": "Admin İstifadəçi",
        "sidebar_active": "Aktiv",
        "sidebar_manage_faces": "Şəxsləri İdarə Et",
        "sidebar_settings": "Profil və Tənzimləmələr",
        "sidebar_statistics": "Statistika",
        "sidebar_registered_faces": "Qeydiyyatlı üzlər",
        "sidebar_total_detections": "Ümumi aşkarlamalar",
        "sidebar_exit": "Çıxış",
        
        # Dashboard Cards
        "card_start_camera": "Kameranı Başlat",
        "card_start_camera_desc": "Üz tanıma sistemini aktivləşdir",
        "card_add_face": "Üz Əlavə Et",
        "card_add_face_desc": "Yeni şəxs qeydiyyatı",
        "card_view_logs": "Jurnalları Gör",
        "card_view_logs_desc": "Hadisə tarixçəsini nəzərdən keçir",
        "card_stop_system": "Sistemi Dayandır",
        
        # Dashboard Other
        "welcome_title": "Xoş Gəldiniz, Admin",
        "welcome_subtitle": "FacePro ilə təhlükəsizliyiniz zəmanət altında",
        "recent_activity": "Son Hadisələr",
        "logs_title": "Sistem Jurnalları və Hadisələr",
        "export_csv": "İxrac Et (CSV)",
        "start_system": "Sistemi Başlat",
        "filter_all": "Hamısı",
        "filter_known": "Tanınmış",
        "filter_unknown": "Naməlum",
        "logs_entries": "giriş",
        
        # Settings
        "settings_title": "Ayarlar",
        "tab_general": "Ümumi",
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
        "msg_success": "Uğurlu",
        "msg_language_changed": "Dil uğurla dəyişdirildi!"
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
        
        # Main Window / Dashboard
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
        
        # Dashboard Tabs & Sidebar
        "tab_home": "Главная",
        "tab_camera": "Камера",
        "tab_logs": "Журналы",
        "sidebar_admin": "Администратор",
        "sidebar_active": "Активен",
        "sidebar_manage_faces": "Управление Лицами",
        "sidebar_settings": "Профиль и Настройки",
        "sidebar_statistics": "Статистика",
        "sidebar_registered_faces": "Зарег. лица",
        "sidebar_total_detections": "Всего обнаружений",
        "sidebar_exit": "Выход",
        
        # Dashboard Cards
        "card_start_camera": "Запустить Камеру",
        "card_start_camera_desc": "Активировать систему распознавания",
        "card_add_face": "Добавить Лицо",
        "card_add_face_desc": "Зарегистрировать нового человека",
        "card_view_logs": "Журналы",
        "card_view_logs_desc": "Просмотреть историю событий",
        "card_stop_system": "Остановить Систему",
        
        # Dashboard Other
        "welcome_title": "Добро пожаловать, Админ",
        "welcome_subtitle": "Ваша безопасность гарантирована с FacePro",
        "recent_activity": "Недавняя Активность",
        "logs_title": "Журналы Системы",
        "export_csv": "Экспорт (CSV)",
        "start_system": "Запустить Систему",
        "filter_all": "Все",
        "filter_known": "Известные",
        "filter_unknown": "Неизвестные",
        "logs_entries": "записей",
        
        # Settings
        "settings_title": "Настройки",
        "tab_general": "Общие",
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
        "msg_success": "Успешно",
        "msg_language_changed": "Язык успешно изменён!"
    }
}


class Translator(QObject):
    """Multilingual translator with live update support."""
    
    language_changed = pyqtSignal(str)  # Emits new language code
    
    def __init__(self):
        super().__init__()
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
    
    def set_language(self, lang_code: str):
        """
        Dili canlı olaraq dəyişdirir və signal göndərir.
        """
        if lang_code in TRANSLATIONS and lang_code != self._language:
            self._language = lang_code
            self.language_changed.emit(lang_code)
    
    @property
    def current_language(self) -> str:
        return self._language


# Global instance
_translator = Translator()

def tr(key: str) -> str:
    """Qlobal tərcümə funksiyası."""
    return _translator.tr(key)

def set_language(lang_code: str):
    """Dili canlı dəyişdir."""
    _translator.set_language(lang_code)

def get_translator() -> Translator:
    """Translator instance-nı qaytarır (signal bağlantısı üçün)."""
    return _translator

