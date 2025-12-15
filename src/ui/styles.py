"""
FacePro Styles Module
PyQt6 üçün Dark Theme və UI styles.
"""

# Dark Theme Color Palette
COLORS = {
    # Primary Colors
    'primary': '#3B82F6',       # Blue
    'primary_hover': '#2563EB',
    'primary_dark': '#1D4ED8',
    
    # Accent Colors
    'success': '#22C55E',       # Green
    'warning': '#F59E0B',       # Amber
    'danger': '#EF4444',        # Red
    'info': '#06B6D4',          # Cyan
    
    # Background Colors
    'bg_dark': '#0F172A',       # Darkest
    'bg_medium': '#1E293B',     # Medium dark
    'bg_light': '#334155',      # Light dark
    'bg_card': '#1E293B',       # Card background
    
    # Text Colors
    'text_primary': '#F8FAFC',  # White
    'text_secondary': '#94A3B8', # Gray
    'text_muted': '#64748B',    # Muted
    
    # Border Colors
    'border': '#334155',
    'border_light': '#475569',
    
    # Status Colors
    'online': '#22C55E',
    'offline': '#EF4444',
    'unknown': '#F59E0B',
}


# Main Application StyleSheet
DARK_THEME = f"""
/* ===== Global Styles ===== */
QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

/* ===== Labels ===== */
QLabel {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    padding: 2px;
}}

QLabel[class="title"] {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

QLabel[class="subtitle"] {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}

/* ===== Buttons ===== */
QPushButton {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_muted']};
}}

QPushButton[class="secondary"] {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {COLORS['border_light']};
}}

QPushButton[class="danger"] {{
    background-color: {COLORS['danger']};
}}

QPushButton[class="danger"]:hover {{
    background-color: #DC2626;
}}

QPushButton[class="success"] {{
    background-color: {COLORS['success']};
}}

/* ===== Line Edits ===== */
QLineEdit {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {COLORS['primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_muted']};
}}

/* ===== Text Edits ===== */
QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
}}

/* ===== Combo Box ===== */
QComboBox {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 32px;
}}

QComboBox:hover {{
    border-color: {COLORS['border_light']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['primary']};
}}

/* ===== Spin Box ===== */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
}}

/* ===== Check Box ===== */
QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['bg_medium']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

/* ===== Radio Button ===== */
QRadioButton {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['bg_medium']};
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

/* ===== Slider ===== */
QSlider::groove:horizontal {{
    height: 6px;
    background-color: {COLORS['bg_light']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background-color: {COLORS['primary']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background-color: {COLORS['primary']};
    border-radius: 3px;
}}

/* ===== Progress Bar ===== */
QProgressBar {{
    background-color: {COLORS['bg_light']};
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 4px;
}}

/* ===== Scroll Bar ===== */
QScrollBar:vertical {{
    background-color: {COLORS['bg_dark']};
    width: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_light']};
    border-radius: 6px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['border_light']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_dark']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['bg_light']};
    border-radius: 6px;
    min-width: 20px;
}}

/* ===== Tab Widget ===== */
QTabWidget::pane {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 10px;
}}

QTabBar::tab {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
}}

QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

/* ===== Group Box ===== */
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding: 15px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 5px;
    color: {COLORS['text_primary']};
}}

/* ===== List Widget ===== */
QListWidget {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 5px;
}}

QListWidget::item {{
    padding: 8px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {COLORS['primary']};
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_light']};
}}

/* ===== Table Widget ===== */
QTableWidget {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    gridline-color: {COLORS['border']};
}}

QTableWidget::item {{
    padding: 8px;
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    padding: 10px;
    border: none;
    font-weight: bold;
}}

/* ===== Menu Bar ===== */
QMenuBar {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    padding: 5px;
}}

QMenuBar::item {{
    padding: 8px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_light']};
}}

QMenu {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 5px;
}}

QMenu::item {{
    padding: 8px 30px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['primary']};
}}

/* ===== Tool Tip ===== */
QToolTip {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border']};
}}

/* ===== Dialog ===== */
QDialog {{
    background-color: {COLORS['bg_dark']};
}}

/* ===== Splitter ===== */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}
"""


# Video Widget Overlay Styles (for drawing)
VIDEO_OVERLAY_STYLE = {
    'font_family': 'Segoe UI',
    'font_size': 12,
    'font_color': (255, 255, 255),  # BGR
    'bbox_thickness': 2,
    'known_color': (0, 255, 0),     # Green (BGR)
    'unknown_color': (0, 0, 255),   # Red (BGR)
    'cat_color': (0, 165, 255),     # Orange (BGR)
    'dog_color': (0, 255, 255),     # Yellow (BGR)
}


def get_status_color(status: str) -> str:
    """Status üçün rəng qaytarır."""
    return {
        'online': COLORS['online'],
        'connected': COLORS['online'],
        'offline': COLORS['offline'],
        'disconnected': COLORS['offline'],
        'warning': COLORS['warning'],
        'error': COLORS['danger'],
    }.get(status.lower(), COLORS['unknown'])


def apply_theme(widget):
    """Widget-ə dark theme tətbiq edir."""
    widget.setStyleSheet(DARK_THEME)
