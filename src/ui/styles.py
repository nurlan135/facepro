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
    background-color: {COLORS['bg_light']};
    border-radius: 10px;
    border: none;
    padding: 10px;
}}

QListWidget[class="activity_feed"]::item {{
    background-color: {COLORS['bg_medium']};
    margin-bottom: 8px;
    border-radius: 6px;
    padding: 10px;
    border: 1px solid {COLORS['border']};
}}

QListWidget[class="activity_feed"]::item:hover {{
    border: 1px solid {COLORS['primary']};
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
