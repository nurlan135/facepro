"""
FacePro Styles Module
CYBER-BRUTALIST EDITION
High-Fidelity Security Dashboard Styles (Ported from Tailwind CSS concept)
"""

# Cyber-Brutalist Color Palette (Based on HTML Concept)
COLORS = {
    # Base
    'bg_void': '#020202',        # Deepest Black
    'bg_panel': '#0a0a0f',       # Panel Background
    'bg_overlay': 'rgba(10, 10, 15, 0.85)',
    
    # Accents
    'cyber_cyan': '#00F0FF',     # Main UI Elements
    'acid_green': '#CCFF00',     # Success / Safe / Admin
    'alert_red': '#FF3300',      # Danger / Intrusion / Unknown
    
    # Text
    'text_main': '#E0E0E0',
    'text_muted': '#6b7280',     # slate-500
    
    # Legacy / Compatibility mappings
    'bg_dark': '#0a0a0f',
    'bg_light': '#1a1a1f',
    'bg_medium': '#121215',
    'text_primary': '#E0E0E0',
    'text_secondary': '#6b7280',
    'primary': '#00F0FF',
    'primary_hover': '#00C0CC',
    'success': '#CCFF00',
    'danger': '#FF3300',
    'warning': '#FFCC00',
    'border': 'rgba(0, 240, 255, 0.3)',
    'online': '#CCFF00',
    'offline': '#6b7280',
    'unknown': '#FF3300',
    'surface': '#0a0a0f',
    'surface_light': '#1a1a1f',
    
    # Missing Legacy Keys (Fix for KeyErrors)
    'border_light': 'rgba(255, 255, 255, 0.1)',
    'bg_card': '#0a0a0f',
    'input_bg': '#121215',
    'input_border': 'rgba(0, 240, 255, 0.3)',
    
    # Tech Elements
    'grid_line': 'rgba(0, 240, 255, 0.1)',
    'border_tech': 'rgba(0, 240, 255, 0.3)',
}

# Key Fonts to fallback to if custom font isn't available
# Ideally: Rajdhani -> Segoe UI, JetBrains Mono -> Consolas
FONT_HEADER = "Rajdhani, 'Segoe UI', sans-serif"
FONT_MONO = "'JetBrains Mono', Consolas, 'Courier New', monospace"


# Main Application StyleSheet (QSS)
CYBER_THEME = f"""
/* ===== Global Styles ===== */
QWidget {{
    background-color: {COLORS['bg_void']};
    color: {COLORS['text_main']};
    font-family: {FONT_HEADER};
    font-size: 14px;
}}

QMainWindow {{
    background-color: {COLORS['bg_void']};
}}

/* ===== Header ===== */
QFrame[class="header"] {{
    background-color: {COLORS['bg_panel']};
    border-bottom: 1px solid {COLORS['border_tech']};
}}

QLabel[class="brand_title"] {{
    font-family: {FONT_HEADER};
    font-size: 24px;
    font-weight: bold;
    color: white;
    letter-spacing: 2px;
}}

QLabel[class="brand_subtitle"] {{
    font-family: {FONT_MONO};
    font-size: 10px;
    color: {COLORS['text_muted']};
    letter-spacing: 1px;
}}

/* ===== Sidebar ===== */
QWidget[class="sidebar"] {{
    background-color: {COLORS['bg_panel']};
    border-right: 1px solid {COLORS['border_tech']};
}}

QPushButton[class="nav_btn"] {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 10px;
    qproperty-iconSize: 24px 24px;
}}

QPushButton[class="nav_btn"]:hover {{
    background-color: rgba(0, 240, 255, 0.1);
    color: {COLORS['cyber_cyan']};
    border: 1px solid {COLORS['cyber_cyan']};
}}

QPushButton[class="nav_btn_active"] {{
    background-color: rgba(0, 240, 255, 0.15);
    color: {COLORS['cyber_cyan']};
    border-left: 2px solid {COLORS['cyber_cyan']};
}}

/* ===== Content Area ===== */
QWidget[class="content_area"] {{
    background-color: {COLORS['bg_void']};
}}

/* ===== Video Grid Cards ===== */
QFrame[class="video_container"] {{
    background-color: #000000;
    border: 1px solid #1a1a1a;
}}
QFrame[class="video_container"]:hover {{
    border: 1px solid {COLORS['cyber_cyan']};
}}

/* ===== Event Panel (Right Side) ===== */
QWidget[class="event_panel"] {{
    background-color: {COLORS['bg_panel']};
    border-left: 1px solid {COLORS['border_tech']};
}}

QLabel[class="panel_header"] {{
    font-family: {FONT_MONO};
    font-size: 14px;
    font-weight: bold;
    color: {COLORS['cyber_cyan']};
    padding: 10px;
    background-color: rgba(0, 240, 255, 0.05);
    border-bottom: 1px solid {COLORS['border_tech']};
}}

/* Event Cards */
QFrame[class="event_card"] {{
    background-color: rgba(255, 255, 255, 0.03);
    border-left: 2px solid transparent;
    margin-bottom: 8px;
    padding: 2px;
}}

QFrame[class="event_card"]:hover {{
    background-color: rgba(255, 255, 255, 0.08);
}}

/* Known Person Card */
QFrame[class="event_card_known"] {{
    border-left: 2px solid {COLORS['acid_green']};
}}

/* Unknown/Intrusion Card */
QFrame[class="event_card_alert"] {{
    border-left: 2px solid {COLORS['alert_red']};
    background-color: rgba(255, 51, 0, 0.05);
}}

QLabel[class="event_name_known"] {{
    font-family: {FONT_HEADER};
    font-weight: bold;
    font-size: 14px;
    color: {COLORS['acid_green']};
}}

QLabel[class="event_name_alert"] {{
    font-family: {FONT_HEADER};
    font-weight: bold;
    font-size: 14px;
    color: {COLORS['alert_red']};
}}

QLabel[class="event_meta"] {{
    font-family: {FONT_MONO};
    font-size: 10px;
    color: {COLORS['text_muted']};
}}


/* ===== Scrollbars (Custom Tech Look) ===== */
QScrollBar:vertical {{
    border: none;
    background: {COLORS['bg_void']};
    width: 6px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border_tech']};
    min-height: 20px;
    border-radius: 0px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['cyber_cyan']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""

# Alias for backward compatibility
DARK_THEME = CYBER_THEME

# Overlay Drawing Colors (OpenCV BGR)
VIDEO_OVERLAY_STYLE = {
    'font_face': 0, # FONT_HERSHEY_SIMPLEX
    'font_scale': 0.5,
    'thickness': 1,
    'color_known': (0, 255, 204),    # Acid Green-ish (BGR: 204, 255, 0)
    'color_unknown': (0, 51, 255),   # Red (BGR: 255, 51, 0)
    'color_ui': (255, 240, 0),       # Cyan (BGR: 0, 240, 255)
}

def apply_theme(widget):
    """Widget-ə Cyber-Brutalist theme tətbiq edir."""
    widget.setStyleSheet(CYBER_THEME)

def get_color_hex(name: str) -> str:
    return COLORS.get(name, '#FFFFFF')

def get_status_color(status: str) -> str:
    """Status-a görə rəng kodunu qaytarır."""
    name = status.lower()
    if name in ['connected', 'online', 'active', 'secure']:
        return COLORS['acid_green']
    elif name in ['connecting', 'reconnecting', 'warning']:
        return COLORS['warning']
    elif name in ['failed', 'offline', 'error', 'intrusion']:
        return COLORS['alert_red']
    return COLORS['text_muted']
