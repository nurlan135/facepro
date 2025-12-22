"""
FacePro Toast Notification Widget
----------------------------------
Pop-up notification widget for user-facing error messages.
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, pyqtProperty
from PyQt6.QtGui import QColor, QFont

from src.ui.styles import COLORS
from src.utils.error_service import ErrorEvent, ErrorLevel


class ToastWidget(QWidget):
    """
    Pop-up notification widget.
    
    Ekranın sağ-aşağı küncündə görünür və avtomatik yox olur.
    """
    
    # Level-ə görə rənglər
    LEVEL_COLORS = {
        ErrorLevel.INFO: "#3498db",      # Blue
        ErrorLevel.WARNING: "#f39c12",   # Orange
        ErrorLevel.ERROR: "#e74c3c",     # Red
        ErrorLevel.CRITICAL: "#8e44ad"   # Purple
    }
    
    # Level-ə görə ikonlar
    LEVEL_ICONS = {
        ErrorLevel.INFO: "ℹ️",
        ErrorLevel.WARNING: "⚠️",
        ErrorLevel.ERROR: "❌",
        ErrorLevel.CRITICAL: "🔴"
    }
    
    def __init__(self, event: ErrorEvent, parent=None):
        super().__init__(parent)
        
        self._event = event
        self._opacity = 1.0
        
        self._setup_ui()
        self._setup_animation()
        self._start_auto_dismiss()
    
    def _setup_ui(self):
        """UI setup."""
        # Window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Fixed width
        self.setFixedWidth(350)
        
        # Main container
        container = QWidget()
        container.setObjectName("toastContainer")
        
        # Layout
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(16, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(self.LEVEL_ICONS.get(self._event.level, "ℹ️"))
        icon_label.setFont(QFont("Segoe UI Emoji", 20))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(icon_label)
        
        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        # Title
        title_label = QLabel(self._event.title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setWordWrap(True)
        text_layout.addWidget(title_label)
        
        # Message
        msg_label = QLabel(self._event.message)
        msg_label.setFont(QFont("Segoe UI", 10))
        msg_label.setStyleSheet("color: rgba(255, 255, 255, 0.85);")
        msg_label.setWordWrap(True)
        text_layout.addWidget(msg_label)
        
        # Action button (optional)
        if self._event.action_label:
            action_btn = QPushButton(self._event.action_label)
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.2);
                    color: white;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.3);
                }
            """)
            action_btn.clicked.connect(self._on_action)
            text_layout.addWidget(action_btn)
        
        main_layout.addLayout(text_layout, 1)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.2);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.4);
            }
        """)
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Styling
        bg_color = self.LEVEL_COLORS.get(self._event.level, "#3498db")
        container.setStyleSheet(f"""
            #toastContainer {{
                background-color: {bg_color};
                border-radius: 10px;
            }}
        """)
        
        # Add shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)
        
        # Final layout
        final_layout = QVBoxLayout(self)
        final_layout.setContentsMargins(10, 10, 10, 10)
        final_layout.addWidget(container)
    
    def _setup_animation(self):
        """Animation setup (fade-out)."""
        self._fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self._fade_animation.setDuration(300)
        self._fade_animation.finished.connect(self.close)
    
    def _start_auto_dismiss(self):
        """Avtomatik yox olma timer-i."""
        # Səviyyəyə görə müddət
        if self._event.level == ErrorLevel.INFO:
            duration = 4000
        elif self._event.level == ErrorLevel.WARNING:
            duration = 6000
        elif self._event.level == ErrorLevel.ERROR:
            duration = 8000
        else:  # CRITICAL
            duration = 12000
        
        QTimer.singleShot(duration, self._fade_out)
    
    def _fade_out(self):
        """Fade-out animation başlat."""
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.start()
    
    def _on_action(self):
        """Action düyməsinə klik."""
        if self._event.action_callback:
            try:
                self._event.action_callback()
            except Exception as e:
                print(f"Toast action error: {e}")
        self.close()
    
    def show_at_position(self, x: int, y: int):
        """Müəyyən mövqedə göstər."""
        self.move(x, y)
        self.show()


class ToastManager:
    """
    Toast notification manager.
    
    Ekranda eyni anda çoxlu toast göstərmək üçün.
    """
    
    def __init__(self, parent=None):
        self._parent = parent
        self._active_toasts: list[ToastWidget] = []
        self._toast_spacing = 10
        self._margin_right = 20
        self._margin_bottom = 20
    
    def show_toast(self, event: ErrorEvent):
        """
        Yeni toast göstər.
        
        Args:
            event: ErrorEvent
        """
        toast = ToastWidget(event, self._parent)
        toast.destroyed.connect(lambda: self._on_toast_closed(toast))
        
        self._active_toasts.append(toast)
        self._reposition_toasts()
        
        toast.show()
    
    def _on_toast_closed(self, toast: ToastWidget):
        """Toast bağlandıqda."""
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
            self._reposition_toasts()
    
    def _reposition_toasts(self):
        """Toast-ları yenidən yerləşdir."""
        if not self._active_toasts:
            return
        
        # Get screen geometry
        screen = QApplication.primaryScreen()
        if not screen:
            return
        
        screen_rect = screen.availableGeometry()
        
        # Position from bottom-right
        current_y = screen_rect.bottom() - self._margin_bottom
        
        for toast in reversed(self._active_toasts):
            toast_height = toast.sizeHint().height()
            current_y -= toast_height
            
            x = screen_rect.right() - toast.width() - self._margin_right
            y = current_y
            
            toast.move(x, y)
            current_y -= self._toast_spacing
    
    def clear_all(self):
        """Bütün toast-ları bağla."""
        for toast in self._active_toasts[:]:
            toast.close()
        self._active_toasts.clear()
