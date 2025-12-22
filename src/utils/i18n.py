
import json
import os
import sys
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from .helpers import load_config
from .logger import get_logger

logger = get_logger()

# Global translator instance
_translator = None

class Translator(QObject):
    language_changed = pyqtSignal(str)

    @property
    def current_language(self) -> str:
        return self._current_lang

    def __init__(self):
        super().__init__()
        self._translations: Dict[str, Any] = {}
        self._current_lang = "en"
        self._flattened_cache: Dict[str, str] = {}
        self._load_all_translations()

    def _load_all_translations(self):
        """Locales qovluğundakı JSON fayllarını yükləyir."""
        # Calculate locales path relative to project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        locales_dir = os.path.join(base_dir, "locales")
        
        supported_langs = ["en", "az", "ru"]
        
        for lang in supported_langs:
            file_path = os.path.join(locales_dir, f"{lang}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self._translations[lang] = json.load(f)
                    logger.info(f"Loaded translations for language: {lang}")
                except Exception as e:
                    logger.error(f"Failed to load translations for {lang}: {e}")
                    self._translations[lang] = {}
            else:
                logger.warning(f"Translation file not found: {file_path}")
                self._translations[lang] = {}

    def load_language(self, lang_code: str):
        """Dili dəyişir və keşlənmiş açarları təmizləyir."""
        if lang_code in self._translations:
            self._current_lang = lang_code
            self._flattened_cache = self._flatten_dict(self._translations[lang_code])
            # Add backend compatibility mapping (old keys -> new structure)
            self._add_backward_compatibility()
            
            self.language_changed.emit(lang_code)
            logger.info(f"Language switched to: {lang_code}")
        else:
            logger.error(f"Language {lang_code} not found in loaded translations.")

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, str]:
        """Nested dictionary-ni düz (flat) struktura çevirir (dot notation üçün)."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, str(v)))
        return dict(items)

    def _add_backward_compatibility(self):
        """
        Köhnə koddakı 'key_name' çağırışlarını yeni 'group.key' formatına xəritələyir.
        This ensures old calls like tr('menu_file') still work by mapping to 'menu.file'.
        """
        mapping = {
            # Menu
            "menu_file": "menu.file",
            "menu_view": "menu.view", 
            "menu_tools": "menu.tools",
            "menu_help": "menu.help",
            "action_exit": "menu.exit",
            "action_faces_add": "menu.faces_add",
            "action_faces_manage": "menu.faces_manage",
            "action_export_events": "menu.export_events",
            "action_license_info": "menu.license_info",
            
            # Dashboard Tabs
            "tab_home": "sidebar.home",
            "tab_camera": "sidebar.camera",
            "tab_logs": "sidebar.logs",
            
             # Sidebar
            "sidebar_admin": "sidebar.admin",
            "sidebar_active": "sidebar.active",
            "sidebar_manage_faces": "sidebar.manage_faces",
            "sidebar_settings": "sidebar.settings",
            "sidebar_statistics": "sidebar.statistics",
            "sidebar_registered_faces": "sidebar.registered_faces",
            "sidebar_total_detections": "sidebar.total_detections",
            "sidebar_exit": "sidebar.exit",
            "sidebar_logout": "sidebar.logout",
            "sidebar_user_management": "sidebar.user_management",
            "sidebar_change_password": "sidebar.change_password",
            
             # Dashboard Cards
            "card_start_camera": "dashboard.cards.start_camera",
            "card_start_camera_desc": "dashboard.cards.start_camera_desc",
            "card_add_face": "dashboard.cards.add_face",
            "card_add_face_desc": "dashboard.cards.add_face_desc",
            "card_view_logs": "dashboard.cards.view_logs",
            "card_view_logs_desc": "dashboard.cards.view_logs_desc",
            "card_stop_system": "dashboard.cards.stop_system",

            # Dashboard Other
            "welcome_title": "dashboard.welcome_title",
            "welcome_subtitle": "dashboard.welcome_subtitle",
            "recent_activity": "dashboard.recent_activity",
            "logs_title": "dashboard.logs_title",
            "export_csv": "dashboard.export_csv",
            "start_system": "dashboard.start_system",
            "filter_all": "dashboard.filter_all",
            "filter_known": "dashboard.filter_known",
            "filter_unknown": "dashboard.filter_unknown",
            "logs_entries": "dashboard.logs_entries",
            "btn_load_more": "dashboard.btn_load_more",

             # Settings
            "settings_title": "settings.title",
            "tab_general": "settings.tab_general",
            "tab_ai": "settings.tab_ai",
            "tab_storage": "settings.tab_storage",
            "tab_notifications": "settings.tab_notifications",
            "tab_audit": "settings.tab_audit",
            "audit_logs_title": "settings.audit_logs_title",
            "refresh": "settings.refresh",
            "audit_timestamp": "settings.audit_timestamp",
            "audit_user": "settings.audit_user",
            "audit_action": "settings.audit_action",
            "audit_details": "settings.audit_details",
            "btn_save": "settings.btn_save",
            "btn_apply": "settings.btn_save", # Map to save if apply not exists
            "btn_cancel": "settings.btn_cancel",
            "lbl_language": "settings.language",
            "lbl_theme": "settings.theme",
            "lbl_app_name": "settings.app_name",
            "lbl_motion_sensitive": "settings.motion_sensitive",
            "lbl_face_conf": "settings.face_conf",
            "lbl_classes": "settings.classes",
            "lbl_telegram_token": "settings.telegram_token",
            "lbl_chat_id": "settings.chat_id",
            "btn_test_conn": "settings.test_conn",
            "lbl_gsm_port": "settings.gsm_port",
            "lbl_gsm_phone": "settings.gsm_phone",
            "msg_saved": "settings.msg_saved",
            "msg_restart_required": "settings.msg_restart",
            "msg_restart_detail": "settings.msg_restart_detail",
            "msg_error": "common.msg_error",
            "msg_success": "common.msg_success",
            "msg_language_changed": "common.msg_language_changed",

            # Login
            "login_title": "login.title",
            "login_subtitle": "login.subtitle",
            "login_username": "login.username",
            "login_password": "login.password",
            "login_username_placeholder": "login.username_placeholder",
            "login_password_placeholder": "login.password_placeholder",
            "login_btn_signin": "login.sign_in",
            "login_btn_exit": "login.exit",
            "login_signing_in": "login.signing_in",
            "login_error_username": "login.error_username",
            "login_error_password": "login.error_password",
            "login_account_locked": "login.account_locked",

             # Setup
            "setup_title": "setup.title",
            "setup_subtitle": "setup.subtitle",
            "setup_welcome": "setup.welcome",
            "setup_username": "setup.username",
            "setup_password": "setup.password",
            "setup_confirm": "setup.confirm",
            "setup_username_placeholder": "setup.username_placeholder",
            "setup_password_placeholder": "setup.password_placeholder",
            "setup_confirm_placeholder": "setup.confirm_placeholder",
            "setup_btn_create": "setup.btn_create",
            "setup_btn_exit": "setup.btn_exit",
            "setup_creating": "setup.creating",
            "setup_success": "setup.success",
            "setup_hint_username_short": "setup.hint_username_short",
            "setup_hint_username_valid": "setup.hint_username_valid",
            "setup_hint_password_short": "setup.hint_password_short",
            "setup_hint_password_valid": "setup.hint_password_valid",
            "setup_hint_password_mismatch": "setup.hint_password_mismatch",
            "setup_hint_password_match": "setup.hint_password_match",

             # User Mgmt
            "user_mgmt_title": "user_management.title",
            "user_mgmt_subtitle": "user_management.subtitle",
            "user_mgmt_add": "user_management.add",
            "user_mgmt_edit": "user_management.edit",
            "user_mgmt_delete": "user_management.delete",
            "user_mgmt_close": "user_management.close",
            "user_mgmt_col_username": "user_management.col_username",
            "user_mgmt_col_role": "user_management.col_role",
            "user_mgmt_col_created": "user_management.col_created",
            "user_mgmt_col_actions": "user_management.col_actions",
            "user_mgmt_role_admin": "user_management.role_admin",
            "user_mgmt_role_operator": "user_management.role_operator",
            "user_mgmt_confirm_delete": "user_management.confirm_delete",
            "user_mgmt_delete_msg": "user_management.delete_msg",

            # Change Pwd
            "change_pwd_title": "change_password.title",
            "change_pwd_subtitle": "change_password.subtitle",
            "change_pwd_current": "change_password.current",
            "change_pwd_new": "change_password.new",
            "change_pwd_confirm": "change_password.confirm",
            "change_pwd_current_placeholder": "change_password.current_placeholder",
            "change_pwd_new_placeholder": "change_password.new_placeholder",
            "change_pwd_confirm_placeholder": "change_password.confirm_placeholder",
            "change_pwd_btn_change": "change_password.btn_change",
            "change_pwd_btn_cancel": "change_password.btn_cancel",
            "change_pwd_changing": "change_password.changing",
            "change_pwd_done": "change_password.done",
            "change_pwd_err_current": "change_password.err_current",
            "change_pwd_err_new": "change_password.err_new",
            "change_pwd_err_min_chars": "change_password.err_min_chars",
            "change_pwd_err_mismatch": "change_password.err_mismatch",
            "change_pwd_err_same": "change_password.err_same",
            "change_pwd_err_no_user": "change_password.err_no_user",

            # Add User
            "add_user_title": "add_user.title",
            "edit_user_title": "add_user.edit_title",
            "user_field_username": "add_user.field_username",
            "user_field_password": "add_user.field_password",
            "user_field_new_password": "add_user.field_new_password",
            "user_field_role": "add_user.field_role",
            "user_placeholder_username": "add_user.placeholder_username",
            "user_placeholder_password": "add_user.placeholder_password",
            "user_placeholder_new_password": "add_user.placeholder_new_password",
            "user_btn_add": "add_user.btn_add",
            "user_btn_save": "add_user.btn_save",
            "user_btn_cancel": "add_user.btn_cancel",
            "user_adding": "add_user.adding",
            "user_saving": "add_user.saving",
            "user_err_username_short": "add_user.err_username_short",
            "user_err_password_short": "add_user.err_password_short",
            "user_delete_cannot_undo": "add_user.delete_cannot_undo",
            "user_error_title": "add_user.error_title",

            # Gait
            "gait_recognition": "gait.recognition",
            "gait_enabled": "gait.enabled",
            "gait_threshold": "gait.threshold",
            "gait_sequence_length": "gait.sequence_length",
            "gait_analyzing": "gait.analyzing",
            "gait_identified": "gait.identified",
            "gait_settings": "gait.settings",
            "gait_threshold_desc": "gait.threshold_desc",
            "gait_sequence_desc": "gait.sequence_desc",
            "identification_method_face": "identification.method_face",
            "identification_method_reid": "identification.method_reid",
            "identification_method_gait": "identification.method_gait",
            "identification_method_unknown": "identification.method_unknown",

            # Camera Dialog
            "select_camera_type": "camera_dialog.select_type",
            "select_camera_type_desc": "camera_dialog.select_type_desc",
            "rtsp_config_title": "camera_dialog.rtsp_config_title",
            "local_camera_title": "camera_dialog.local_camera_title",
            "scanning_cameras": "camera_dialog.scanning",
            "no_cameras_found": "camera_dialog.no_cameras",
            "test_connection": "camera_dialog.test_connection",
            "connection_success": "camera_dialog.connection_success",
            "connection_failed": "camera_dialog.connection_failed",
            "connection_timeout": "camera_dialog.connection_timeout",
            "auth_failed": "camera_dialog.auth_failed",
            "select_this_camera": "camera_dialog.select_this",
            "ip_address": "camera_dialog.ip_address",
            "port": "camera_dialog.port",
            "username": "camera_dialog.username",
            "password": "camera_dialog.password",
            "brand": "camera_dialog.brand",
            "channel": "camera_dialog.channel",
            "stream_type": "camera_dialog.stream_type",
            "main_stream": "camera_dialog.main_stream",
            "sub_stream": "camera_dialog.sub_stream",
            "url_preview": "camera_dialog.url_preview",
            "back": "camera_dialog.back",
            "save": "camera_dialog.save",
            "invalid_ip": "camera_dialog.invalid_ip",
            "camera_in_use": "camera.in_use",
            "permission_denied": "camera.permission_denied",
            "camera_name": "camera.name",
            "resolution": "camera.resolution",
            "fps": "camera.fps",
            "connection_settings": "camera_dialog.connection_settings",
            "camera_open_failed": "camera.open_failed",
            "frame_read_failed": "camera.frame_read_failed",
            "cancel": "camera_dialog.cancel",

             # Camera Modes
            "camera_control": "camera.control",
            "working_mode": "camera.working_mode",
            "mode_security": "camera.mode_security",
            "mode_baby": "camera.mode_baby",
            "mode_object": "camera.mode_object",
            
            # Camera Action Buttons
            "btn_select_camera": "camera.btn_select",
            "btn_start": "camera.btn_start",
            "btn_stop": "camera.btn_stop",
            "status_no_camera": "camera.status_no_camera",
            "status_camera_selected": "camera.status_selected",

            # RTSP
            "rtsp_test_duration": "rtsp.test_duration",
            "rtsp_example_values": "rtsp.example_values",
            "rtsp_connection_guide": "rtsp.connection_guide",
            "rtsp_quick_start": "rtsp.quick_start",
            "rtsp_quick_start_1": "rtsp.quick_start_1",
            "rtsp_quick_start_2": "rtsp.quick_start_2",
            "rtsp_quick_start_3": "rtsp.quick_start_3",
            "rtsp_quick_start_4": "rtsp.quick_start_4",
            "rtsp_important_notes": "rtsp.important_notes",
            "rtsp_note_network": "rtsp.note_network",
            "rtsp_note_port": "rtsp.note_port",
            "rtsp_note_path": "rtsp.note_path",
            "rtsp_enter_url": "rtsp.enter_url",
            "rtsp_preview_placeholder": "rtsp.preview_placeholder",
            "rtsp_preview_hint": "rtsp.preview_hint",
            "logout_confirm_title": "common.logout_confirm_title",
            "logout_confirm_msg": "common.logout_confirm_msg",
            
            # Enrollment
            "enroll_title": "enrollment.title",
            "enroll_subtitle": "enrollment.subtitle",
            "enroll_group_image": "enrollment.group_image",
            "enroll_btn_select": "enrollment.btn_select",
            "enroll_btn_capture": "enrollment.btn_capture",
            "enroll_group_details": "enrollment.group_details",
            "enroll_field_name": "enrollment.field_name",
            "enroll_placeholder_name": "enrollment.placeholder_name",
            "enroll_field_role": "enrollment.field_role",
            "enroll_placeholder_role": "enrollment.placeholder_role",
            "enroll_field_notes": "enrollment.field_notes",
            "enroll_placeholder_notes": "enrollment.placeholder_notes",
            "enroll_field_status": "enrollment.field_status",
            "enroll_btn_save": "enrollment.btn_save",
            "enroll_btn_cancel": "enrollment.btn_cancel",
            "enroll_status_checking": "enrollment.status_checking",
            "enroll_status_no_face": "enrollment.status_no_face",
            "enroll_status_one_face": "enrollment.status_one_face",
            "enroll_status_multi_face": "enrollment.status_multi_face",
            "enroll_error_load": "enrollment.error_load",
            "enroll_error_no_name": "enrollment.error_no_name",
            "enroll_error_no_image": "enrollment.error_no_image",
            "enroll_success_title": "enrollment.success_title",
            "enroll_success_msg": "enrollment.success_msg",
            "enroll_capture_help": "enrollment.capture_help",

            # Session
            "session_timeout_title": "common.session_timeout_title",
            "session_timeout_msg": "common.session_timeout_msg",
            
             # Others
            "last_events": "common.last_events",
            "camera_feed": "common.camera_feed",
            "events_clear": "common.events_clear",
            "events_export": "common.events_export",
            "lbl_rtsp_url": "camera.rtsp_url",
            "lbl_webcam_id": "camera.webcam_id",
            "btn_test_camera": "camera.test_camera",
        }

        # Cache-ə əlavə edirik
        for old_key, new_path in mapping.items():
            if new_path in self._flattened_cache:
                 self._flattened_cache[old_key] = self._flattened_cache[new_path]

    def tr(self, key: str) -> str:
        """Açar sözə uyğun tərcüməni qaytarır."""
        return self._flattened_cache.get(key, key)

    def get_current_language(self) -> str:
        return self._current_lang

def get_translator() -> Translator:
    global _translator
    if _translator is None:
        _translator = Translator()
        
        # Load saved language from config
        config = load_config()
        lang = config.get('language', 'en')
        _translator.load_language(lang)
        
    return _translator

def tr(key: str) -> str:
    """Helper function for quick translation."""
    return get_translator().tr(key)

def set_language(lang_code: str):
    """Sets the language globally (Wrapper for Translator)."""
    get_translator().load_language(lang_code)