
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
        "sidebar_logout": "Logout",
        "sidebar_user_management": "User Management",
        "sidebar_change_password": "Change Password",
        "logout_confirm_title": "Logout",
        "logout_confirm_msg": "Are you sure you want to logout?",
        "session_timeout_title": "Session Timeout",
        "session_timeout_msg": "Your session has expired due to inactivity. Please login again.",
        
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
        "msg_language_changed": "Language changed successfully!",
        
        # Login Dialog
        "login_title": "FacePro - Login",
        "login_subtitle": "Sign in to continue",
        "login_username": "Username",
        "login_password": "Password",
        "login_username_placeholder": "Enter your username",
        "login_password_placeholder": "Enter your password",
        "login_btn_signin": "Sign In",
        "login_btn_exit": "Exit",
        "login_signing_in": "Signing in...",
        "login_error_username": "Please enter your username",
        "login_error_password": "Please enter your password",
        "login_account_locked": "Account is locked",
        
        # Setup Wizard
        "setup_title": "FacePro - Initial Setup",
        "setup_subtitle": "Initial Setup",
        "setup_welcome": "Welcome! Create your administrator account to get started.",
        "setup_username": "Username",
        "setup_password": "Password",
        "setup_confirm": "Confirm Password",
        "setup_username_placeholder": "Enter admin username (min 3 characters)",
        "setup_password_placeholder": "Enter password (min 6 characters)",
        "setup_confirm_placeholder": "Re-enter password",
        "setup_btn_create": "Create Admin Account",
        "setup_btn_exit": "Exit",
        "setup_creating": "Creating account...",
        "setup_success": "Admin account created successfully!",
        "setup_hint_username_short": "Username must be at least 3 characters",
        "setup_hint_username_valid": "Valid username",
        "setup_hint_password_short": "Password must be at least 6 characters",
        "setup_hint_password_valid": "Valid password",
        "setup_hint_password_mismatch": "Passwords do not match",
        "setup_hint_password_match": "Passwords match",
        
        # User Management
        "user_mgmt_title": "User Management",
        "user_mgmt_subtitle": "Manage user accounts and permissions",
        "user_mgmt_add": "Add User",
        "user_mgmt_edit": "Edit",
        "user_mgmt_delete": "Delete",
        "user_mgmt_close": "Close",
        "user_mgmt_col_username": "Username",
        "user_mgmt_col_role": "Role",
        "user_mgmt_col_created": "Created",
        "user_mgmt_col_actions": "Actions",
        "user_mgmt_role_admin": "Admin",
        "user_mgmt_role_operator": "Operator",
        "user_mgmt_confirm_delete": "Confirm Delete",
        "user_mgmt_delete_msg": "Are you sure you want to delete user",
        
        # Change Password
        "change_pwd_title": "Change Password",
        "change_pwd_subtitle": "Enter your current password and choose a new one",
        "change_pwd_current": "Current Password",
        "change_pwd_new": "New Password",
        "change_pwd_confirm": "Confirm New Password",
        "change_pwd_current_placeholder": "Enter your current password",
        "change_pwd_new_placeholder": "Enter new password (min 6 characters)",
        "change_pwd_confirm_placeholder": "Re-enter new password",
        "change_pwd_btn_change": "Change Password",
        "change_pwd_btn_cancel": "Cancel",
        "change_pwd_changing": "Changing...",
        "change_pwd_done": "Done",
        "change_pwd_err_current": "Please enter your current password",
        "change_pwd_err_new": "Please enter a new password",
        "change_pwd_err_min_chars": "New password must be at least 6 characters",
        "change_pwd_err_mismatch": "New passwords do not match",
        "change_pwd_err_same": "New password must be different from current password",
        "change_pwd_err_no_user": "No user logged in",
        
        # Add/Edit User Dialog
        "add_user_title": "Add New User",
        "edit_user_title": "Edit User",
        "user_field_username": "Username",
        "user_field_password": "Password",
        "user_field_new_password": "New Password (leave empty to keep current)",
        "user_field_role": "Role",
        "user_placeholder_username": "Enter username (min 3 characters)",
        "user_placeholder_password": "Enter password (min 6 characters)",
        "user_placeholder_new_password": "Enter new password (min 6 characters)",
        "user_btn_add": "Add User",
        "user_btn_save": "Save Changes",
        "user_btn_cancel": "Cancel",
        "user_adding": "Adding...",
        "user_saving": "Saving...",
        "user_err_username_short": "Username must be at least 3 characters",
        "user_err_password_short": "Password must be at least 6 characters",
        "user_delete_cannot_undo": "This action cannot be undone.",
        "user_error_title": "Error",
        
        # Gait Recognition
        "gait_recognition": "Gait Recognition",
        "gait_enabled": "Enable Gait Recognition",
        "gait_threshold": "Gait Confidence Threshold",
        "gait_sequence_length": "Gait Sequence Length",
        "gait_analyzing": "Analyzing gait...",
        "gait_identified": "Gait",
        "gait_settings": "Gait Recognition Settings",
        "gait_threshold_desc": "Minimum confidence for gait identification (0.50 - 0.95)",
        "gait_sequence_desc": "Number of frames for gait analysis (20 - 60)",
        "identification_method_face": "Face",
        "identification_method_reid": "Re-ID",
        "identification_method_gait": "Gait",
        "identification_method_unknown": "Unknown"
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
        "sidebar_exit": "Proqramdan Çıx",
        "sidebar_logout": "Hesabdan Çıx",
        "sidebar_user_management": "İstifadəçi İdarəetməsi",
        "sidebar_change_password": "Şifrəni Dəyiş",
        "logout_confirm_title": "Çıxış",
        "logout_confirm_msg": "Çıxış etmək istədiyinizə əminsiniz?",
        "session_timeout_title": "Sessiya Vaxtı Bitdi",
        "session_timeout_msg": "Aktivlik olmadığına görə sessiyanız bitdi. Yenidən daxil olun.",
        
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
        "msg_language_changed": "Dil uğurla dəyişdirildi!",
        
        # Login Dialog
        "login_title": "FacePro - Giriş",
        "login_subtitle": "Davam etmək üçün daxil olun",
        "login_username": "İstifadəçi adı",
        "login_password": "Şifrə",
        "login_username_placeholder": "İstifadəçi adınızı daxil edin",
        "login_password_placeholder": "Şifrənizi daxil edin",
        "login_btn_signin": "Daxil ol",
        "login_btn_exit": "Çıxış",
        "login_signing_in": "Daxil olunur...",
        "login_error_username": "İstifadəçi adını daxil edin",
        "login_error_password": "Şifrəni daxil edin",
        "login_account_locked": "Hesab kilidlənib",
        
        # Setup Wizard
        "setup_title": "FacePro - İlkin Quraşdırma",
        "setup_subtitle": "İlkin Quraşdırma",
        "setup_welcome": "Xoş gəldiniz! Başlamaq üçün administrator hesabı yaradın.",
        "setup_username": "İstifadəçi adı",
        "setup_password": "Şifrə",
        "setup_confirm": "Şifrəni təsdiqlə",
        "setup_username_placeholder": "Admin istifadəçi adı (min 3 simvol)",
        "setup_password_placeholder": "Şifrə daxil edin (min 6 simvol)",
        "setup_confirm_placeholder": "Şifrəni yenidən daxil edin",
        "setup_btn_create": "Admin Hesabı Yarat",
        "setup_btn_exit": "Çıxış",
        "setup_creating": "Hesab yaradılır...",
        "setup_success": "Admin hesabı uğurla yaradıldı!",
        "setup_hint_username_short": "İstifadəçi adı ən azı 3 simvol olmalıdır",
        "setup_hint_username_valid": "Düzgün istifadəçi adı",
        "setup_hint_password_short": "Şifrə ən azı 6 simvol olmalıdır",
        "setup_hint_password_valid": "Düzgün şifrə",
        "setup_hint_password_mismatch": "Şifrələr uyğun gəlmir",
        "setup_hint_password_match": "Şifrələr uyğundur",
        
        # User Management
        "user_mgmt_title": "İstifadəçi İdarəetməsi",
        "user_mgmt_subtitle": "İstifadəçi hesablarını və icazələri idarə edin",
        "user_mgmt_add": "İstifadəçi Əlavə Et",
        "user_mgmt_edit": "Redaktə",
        "user_mgmt_delete": "Sil",
        "user_mgmt_close": "Bağla",
        "user_mgmt_col_username": "İstifadəçi adı",
        "user_mgmt_col_role": "Rol",
        "user_mgmt_col_created": "Yaradılıb",
        "user_mgmt_col_actions": "Əməliyyatlar",
        "user_mgmt_role_admin": "Admin",
        "user_mgmt_role_operator": "Operator",
        "user_mgmt_confirm_delete": "Silməyi Təsdiqlə",
        "user_mgmt_delete_msg": "Bu istifadəçini silmək istədiyinizə əminsiniz",
        
        # Change Password
        "change_pwd_title": "Şifrəni Dəyiş",
        "change_pwd_subtitle": "Cari şifrənizi daxil edin və yeni şifrə seçin",
        "change_pwd_current": "Cari Şifrə",
        "change_pwd_new": "Yeni Şifrə",
        "change_pwd_confirm": "Yeni Şifrəni Təsdiqlə",
        "change_pwd_current_placeholder": "Cari şifrənizi daxil edin",
        "change_pwd_new_placeholder": "Yeni şifrə daxil edin (min 6 simvol)",
        "change_pwd_confirm_placeholder": "Yeni şifrəni yenidən daxil edin",
        "change_pwd_btn_change": "Şifrəni Dəyiş",
        "change_pwd_btn_cancel": "Ləğv Et",
        "change_pwd_changing": "Dəyişdirilir...",
        "change_pwd_done": "Hazır",
        "change_pwd_err_current": "Cari şifrənizi daxil edin",
        "change_pwd_err_new": "Yeni şifrə daxil edin",
        "change_pwd_err_min_chars": "Yeni şifrə ən azı 6 simvol olmalıdır",
        "change_pwd_err_mismatch": "Yeni şifrələr uyğun gəlmir",
        "change_pwd_err_same": "Yeni şifrə cari şifrədən fərqli olmalıdır",
        "change_pwd_err_no_user": "Daxil olmuş istifadəçi yoxdur",
        
        # Add/Edit User Dialog
        "add_user_title": "Yeni İstifadəçi Əlavə Et",
        "edit_user_title": "İstifadəçini Redaktə Et",
        "user_field_username": "İstifadəçi adı",
        "user_field_password": "Şifrə",
        "user_field_new_password": "Yeni Şifrə (saxlamaq üçün boş buraxın)",
        "user_field_role": "Rol",
        "user_placeholder_username": "İstifadəçi adı daxil edin (min 3 simvol)",
        "user_placeholder_password": "Şifrə daxil edin (min 6 simvol)",
        "user_placeholder_new_password": "Yeni şifrə daxil edin (min 6 simvol)",
        "user_btn_add": "İstifadəçi Əlavə Et",
        "user_btn_save": "Dəyişiklikləri Saxla",
        "user_btn_cancel": "Ləğv Et",
        "user_adding": "Əlavə edilir...",
        "user_saving": "Saxlanılır...",
        "user_err_username_short": "İstifadəçi adı ən azı 3 simvol olmalıdır",
        "user_err_password_short": "Şifrə ən azı 6 simvol olmalıdır",
        "user_delete_cannot_undo": "Bu əməliyyat geri qaytarıla bilməz.",
        "user_error_title": "Səhv",
        
        # Gait Recognition
        "gait_recognition": "Yeriş Tanıma",
        "gait_enabled": "Yeriş Tanımanı Aktivləşdir",
        "gait_threshold": "Yeriş Dəqiqlik Həddi",
        "gait_sequence_length": "Yeriş Seqans Uzunluğu",
        "gait_analyzing": "Yeriş analiz edilir...",
        "gait_identified": "Yeriş",
        "gait_settings": "Yeriş Tanıma Ayarları",
        "gait_threshold_desc": "Yeriş tanıma üçün minimum dəqiqlik (0.50 - 0.95)",
        "gait_sequence_desc": "Yeriş analizi üçün kadr sayı (20 - 60)",
        "identification_method_face": "Üz",
        "identification_method_reid": "Re-ID",
        "identification_method_gait": "Yeriş",
        "identification_method_unknown": "Naməlum"
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
        "sidebar_logout": "Выйти",
        "sidebar_user_management": "Управление пользователями",
        "sidebar_change_password": "Изменить пароль",
        "logout_confirm_title": "Выход",
        "logout_confirm_msg": "Вы уверены, что хотите выйти?",
        "session_timeout_title": "Сессия истекла",
        "session_timeout_msg": "Ваша сессия истекла из-за неактивности. Войдите снова.",
        
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
        "msg_language_changed": "Язык успешно изменён!",
        
        # Login Dialog
        "login_title": "FacePro - Вход",
        "login_subtitle": "Войдите для продолжения",
        "login_username": "Имя пользователя",
        "login_password": "Пароль",
        "login_username_placeholder": "Введите имя пользователя",
        "login_password_placeholder": "Введите пароль",
        "login_btn_signin": "Войти",
        "login_btn_exit": "Выход",
        "login_signing_in": "Вход...",
        "login_error_username": "Введите имя пользователя",
        "login_error_password": "Введите пароль",
        "login_account_locked": "Аккаунт заблокирован",
        
        # Setup Wizard
        "setup_title": "FacePro - Начальная настройка",
        "setup_subtitle": "Начальная настройка",
        "setup_welcome": "Добро пожаловать! Создайте учётную запись администратора.",
        "setup_username": "Имя пользователя",
        "setup_password": "Пароль",
        "setup_confirm": "Подтвердите пароль",
        "setup_username_placeholder": "Имя админа (мин. 3 символа)",
        "setup_password_placeholder": "Введите пароль (мин. 6 символов)",
        "setup_confirm_placeholder": "Повторите пароль",
        "setup_btn_create": "Создать аккаунт админа",
        "setup_btn_exit": "Выход",
        "setup_creating": "Создание аккаунта...",
        "setup_success": "Аккаунт админа успешно создан!",
        "setup_hint_username_short": "Имя должно быть не менее 3 символов",
        "setup_hint_username_valid": "Корректное имя",
        "setup_hint_password_short": "Пароль должен быть не менее 6 символов",
        "setup_hint_password_valid": "Корректный пароль",
        "setup_hint_password_mismatch": "Пароли не совпадают",
        "setup_hint_password_match": "Пароли совпадают",
        
        # User Management
        "user_mgmt_title": "Управление пользователями",
        "user_mgmt_subtitle": "Управление учётными записями и разрешениями",
        "user_mgmt_add": "Добавить пользователя",
        "user_mgmt_edit": "Редактировать",
        "user_mgmt_delete": "Удалить",
        "user_mgmt_close": "Закрыть",
        "user_mgmt_col_username": "Имя пользователя",
        "user_mgmt_col_role": "Роль",
        "user_mgmt_col_created": "Создан",
        "user_mgmt_col_actions": "Действия",
        "user_mgmt_role_admin": "Админ",
        "user_mgmt_role_operator": "Оператор",
        "user_mgmt_confirm_delete": "Подтвердите удаление",
        "user_mgmt_delete_msg": "Вы уверены, что хотите удалить пользователя",
        
        # Change Password
        "change_pwd_title": "Изменить пароль",
        "change_pwd_subtitle": "Введите текущий пароль и выберите новый",
        "change_pwd_current": "Текущий пароль",
        "change_pwd_new": "Новый пароль",
        "change_pwd_confirm": "Подтвердите новый пароль",
        "change_pwd_current_placeholder": "Введите текущий пароль",
        "change_pwd_new_placeholder": "Введите новый пароль (мин. 6 символов)",
        "change_pwd_confirm_placeholder": "Повторите новый пароль",
        "change_pwd_btn_change": "Изменить пароль",
        "change_pwd_btn_cancel": "Отмена",
        "change_pwd_changing": "Изменение...",
        "change_pwd_done": "Готово",
        "change_pwd_err_current": "Введите текущий пароль",
        "change_pwd_err_new": "Введите новый пароль",
        "change_pwd_err_min_chars": "Новый пароль должен быть не менее 6 символов",
        "change_pwd_err_mismatch": "Новые пароли не совпадают",
        "change_pwd_err_same": "Новый пароль должен отличаться от текущего",
        "change_pwd_err_no_user": "Пользователь не авторизован",
        
        # Add/Edit User Dialog
        "add_user_title": "Добавить пользователя",
        "edit_user_title": "Редактировать пользователя",
        "user_field_username": "Имя пользователя",
        "user_field_password": "Пароль",
        "user_field_new_password": "Новый пароль (оставьте пустым для сохранения)",
        "user_field_role": "Роль",
        "user_placeholder_username": "Введите имя (мин. 3 символа)",
        "user_placeholder_password": "Введите пароль (мин. 6 символов)",
        "user_placeholder_new_password": "Введите новый пароль (мин. 6 символов)",
        "user_btn_add": "Добавить",
        "user_btn_save": "Сохранить изменения",
        "user_btn_cancel": "Отмена",
        "user_adding": "Добавление...",
        "user_saving": "Сохранение...",
        "user_err_username_short": "Имя должно быть не менее 3 символов",
        "user_err_password_short": "Пароль должен быть не менее 6 символов",
        "user_delete_cannot_undo": "Это действие нельзя отменить.",
        "user_error_title": "Ошибка",
        
        # Gait Recognition
        "gait_recognition": "Распознавание походки",
        "gait_enabled": "Включить распознавание походки",
        "gait_threshold": "Порог точности походки",
        "gait_sequence_length": "Длина последовательности походки",
        "gait_analyzing": "Анализ походки...",
        "gait_identified": "Походка",
        "gait_settings": "Настройки распознавания походки",
        "gait_threshold_desc": "Минимальная точность для идентификации (0.50 - 0.95)",
        "gait_sequence_desc": "Количество кадров для анализа (20 - 60)",
        "identification_method_face": "Лицо",
        "identification_method_reid": "Re-ID",
        "identification_method_gait": "Походка",
        "identification_method_unknown": "Неизвестно"
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

