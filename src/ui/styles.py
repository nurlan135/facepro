"""
FacePro Styles Module
PyQt6 üçün Dark Theme və UI styles.
"""

# Dark Theme Color Palette
# Dark Theme Color Palette
COLORS = {
    # Premium Dark Theme Colors
    'bg_dark': '#121212',       # Main Background (Deepest Black)
    'bg_medium': '#1a1c23',     # Sidebar / Secondary Background
    'bg_light': '#252731',      # Card / Element Background
    'bg_card': '#252731',       # Card Background
    
    # Surface Colors (aliases for compatibility)
    'surface': '#252731',       # Same as bg_light
    'surface_light': '#2c303b', # Slightly lighter surface
    
    # Text Colors
    'text_primary': '#FFFFFF',  # White
    'text_secondary': '#A0AEC0', # Soft Gray
    'text_muted': '#718096',    # Muted Gray
    
    # Accents
    'primary': '#3B82F6',       # Blue (General Primary)
    'primary_hover': '#2563EB',
    
    'success': '#2ecc71',       # Green (Active/Success) - Like image button
    'danger': '#e74c3c',        # Red (Exit/Error) - Like image button
    'warning': '#f1c40f',       # Yellow
    
    'border': '#2d3748',        # Subtle border
    'border_light': '#4a5568',
    
    # Status Colors
    'online': '#2ecc71',
    'offline': '#e74c3c',
    
    # Missing keys added
    'secondary': '#64748B',     # Slate Gray
    'unknown': '#7f8c8d',       # Concrete Gray
}


# Main Application StyleSheet
DARK_THEME = f"""
/* ===== Global Styles ===== */
QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 14px;
}}

QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

/* ===== Sidebar ===== */
QWidget[class="sidebar"] {{
    background-color: {COLORS['bg_medium']};
    border-right: 1px solid {COLORS['border']};
}}

QLabel[class="sidebar_title"] {{
    font-size: 20px;
    font-weight: bold;
    color: {COLORS['primary']};
    padding: 20px 10px;
}}

QPushButton[class="sidebar_btn"] {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    text-align: left;
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
}}

QPushButton[class="sidebar_btn"]:hover {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
}}

QPushButton[class="sidebar_btn_active"] {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['primary']};
    border-left: 3px solid {COLORS['primary']};
    font-weight: bold;
}}

/* ===== Sidebar Profile Card ===== */
QFrame[class="profile_card"] {{
    background-color: transparent;
    border-radius: 10px;
    padding: 10px;
}}

/* ===== Main Dashboard Styles ===== */
QLabel[class="welcome_text"] {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

QLabel[class="tagline"] {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}

/* ===== Action Cards ===== */
QFrame[class="action_card"] {{
    background-color: {COLORS['bg_light']};
    border-radius: 12px;
    border: 1px solid {COLORS['border']};
}}

QFrame[class="action_card"]:hover {{
    border: 1px solid {COLORS['primary']};
    background-color: #2c303b;
}}

/* ===== Activity Feed ===== */
QListWidget[class="activity_feed"] {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QListWidget[class="activity_feed"]::item {{
    background-color: rgba(255, 255, 255, 0.03);
    margin-bottom: 10px;
    border-radius: 10px;
    padding: 5px; /* Inner padding handled by widget */
    border: 1px solid rgba(255, 255, 255, 0.05);
}}

QListWidget[class="activity_feed"]::item:hover {{
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(59, 130, 246, 0.5);
}}

/* Activity Item Components */
QFrame[class="activity_icon_box_success"] {{
    background-color: rgba(46, 204, 113, 0.1);
    border: 1px solid #2ecc71;
    border-radius: 8px;
}}
QFrame[class="activity_icon_box_success"] QLabel {{
    color: #2ecc71;
    font-weight: bold;
    font-size: 18px;
}}

QFrame[class="activity_icon_box_warning"] {{
    background-color: rgba(241, 196, 15, 0.1);
    border: 1px solid #f1c40f;
    border-radius: 8px;
}}
QFrame[class="activity_icon_box_warning"] QLabel {{
    color: #f1c40f;
    font-weight: bold;
    font-size: 18px;
}}

QLabel[class="activity_name"] {{
    font-size: 15px;
    font-weight: bold;
    color: #FFFFFF;
}}

QLabel[class="activity_detail"] {{
    font-size: 12px;
    color: #A0AEC0;
}}

QLabel[class="activity_time"] {{
    font-size: 12px;
    color: #718096;
    font-family: 'Consolas', monospace;
}}

/* ===== Sidebar Section Titles And Stats ===== */
QLabel[class="sidebar_section_title"] {{
    font-size: 12px;
    font-weight: bold;
    color: #4B5563; /* Muted darker gray */
    text-transform: uppercase;
    letter-spacing: 1px;
    padding-left: 5px;
}}

QLabel[class="stat_label"] {{
    color: #A0AEC0;
    font-size: 13px;
    padding-left: 10px;
}}

/* ===== Standard Elements ===== */
QLabel {{ background-color: transparent; }}

QPushButton {{
    background-color: {COLORS['primary']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}}

QPushButton:hover {{ background-color: {COLORS['primary_hover']}; }}

QPushButton[class="logout_btn"] {{
    background-color: {COLORS['danger']};
    color: white;
    font-weight: bold;
}}
QPushButton[class="logout_btn"]:hover {{ background-color: #c0392b; }}

QPushButton[class="status_btn_active"] {{
    background-color: {COLORS['success']};
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    color: white;
}}

/* ===== Tab Bar (Custom Pills) ===== */
QTabWidget::pane {{ border: none; }}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 8px 20px;
    margin-right: 5px;
    border-radius: 16px; 
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

QTabBar::tab:hover {{
    color: white;
    background-color: {COLORS['bg_light']};
}}

/* ===== Filter Buttons ===== */
QPushButton[class="filter_btn"] {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
}}

QPushButton[class="filter_btn"]:hover {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
}}

QPushButton[class="filter_btn_active"] {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
}}

QPushButton[class="filter_btn_active"]:hover {{
    background-color: {COLORS['primary_hover']};
}}

/* ===== Input Fields ===== */
QLineEdit, QComboBox {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
}}

QLineEdit:focus {{
    border: 1px solid {COLORS['primary']};
}}

/* ===== Tables (QTableWidget) ===== */
QTableWidget {{
    background-color: {COLORS['bg_medium']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']}; /* Ensure text is white */
}}

QTableWidget::item {{
    padding: 5px;
    color: {COLORS['text_primary']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: white;
}}

/* Alternating rows override to prevent white text on white bg */
QTableWidget {{
    alternate-background-color: {COLORS['bg_light']}; 
}}

QHeaderView::section {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_secondary']};
    border: none;
    padding: 8px;
    font-weight: bold;
    border-bottom: 2px solid {COLORS['border']};
}}

QPushButton[class="camera_list_btn"] {{
    text-align: left;
    padding: 8px 15px;
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 5px;
}}

QPushButton[class="camera_list_btn"]:hover {{
    border-color: {COLORS['primary']};
}}

QPushButton[class="secondary"] {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[class="secondary"]:hover {{
    background-color: {COLORS['border']};
    color: white;
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
