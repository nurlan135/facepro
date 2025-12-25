"""
FacePro Dashboard Home Page
Cyber-Brutalist Layout: Video Grid + Live Event Log
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt

from src.ui.styles import COLORS, CYBER_THEME
from src.utils.i18n import tr
from src.ui.video_widget import VideoGrid

class HomePage(QWidget):
    """
    Main Dashboard Page.
    Central: Video Grid (CCTV Style)
    Right: Live Event Log (Radar Style)
    """
    
    # Signals (kept for compatibility)
    start_camera_clicked = pyqtSignal()
    add_face_clicked = pyqtSignal()
    view_logs_clicked = pyqtSignal() # Not used in new layout but kept for safety
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- LEFT: VIDEO GRID ---
        grid_container = QWidget()
        grid_container.setProperty("class", "video_container")
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(1, 1, 1, 1) # Thin tech border
        
        # Top Control Bar (Minimal)
        control_bar = self._create_control_bar()
        grid_layout.addWidget(control_bar)
        
        # The Video Content
        self.video_grid = VideoGrid()
        # Set dark background for grid
        self.video_grid.setStyleSheet(f"background-color: {COLORS['bg_void']};")
        grid_layout.addWidget(self.video_grid)
        
        layout.addWidget(grid_container, stretch=75) # 75% width
        
        # --- RIGHT: EVENT LOG ---
        event_panel = QWidget()
        event_panel.setProperty("class", "event_panel")
        event_layout = QVBoxLayout(event_panel)
        event_layout.setContentsMargins(0, 0, 0, 0)
        event_layout.setSpacing(0)
        
        # Panel Header
        self.header_lbl = QLabel(tr("cyber.live_log"))
        self.header_lbl.setProperty("class", "panel_header")
        event_layout.addWidget(self.header_lbl)
        
        # Scrollable Feed
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.feed_container = QWidget()
        self.feed_container.setStyleSheet("background: transparent;")
        self.feed_layout = QVBoxLayout(self.feed_container)
        self.feed_layout.setSpacing(5)
        self.feed_layout.setContentsMargins(10, 10, 10, 10)
        self.feed_layout.addStretch() # Push items up
        
        scroll.setWidget(self.feed_container)
        event_layout.addWidget(scroll)
        
        # Radar/Map Graphic (Decorative)
        radar_box = self._create_radar_widget()
        event_layout.addWidget(radar_box)
        
        layout.addWidget(event_panel, stretch=25) # 25% width

        # Helper to access feed from outside
        self.activity_feed = self 

    def _create_control_bar(self):
        """Creates the thin control strip above videos."""
        bar = QWidget()
        bar.setFixedHeight(40)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Grid Controls
        def make_btn(text, callback):
            btn = QPushButton(text)
            btn.setFixedSize(40, 24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['bg_panel']};
                    color: {COLORS['cyber_cyan']};
                    border: 1px solid {COLORS['border_tech']};
                    font-size: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {COLORS['cyber_cyan']};
                    color: black;
                }}
            """)
            btn.clicked.connect(callback)
            return btn
            
        layout.addWidget(make_btn("1x1", lambda: self.video_grid.set_layout_preset(1)))
        layout.addWidget(make_btn("2x2", lambda: self.video_grid.set_layout_preset(2)))
        layout.addWidget(make_btn("3x3", lambda: self.video_grid.set_layout_preset(3)))
        layout.addWidget(make_btn("4x4", lambda: self.video_grid.set_layout_preset(4)))
        
        layout.addStretch()
        
        # Add Camera / Start Buttons (Mini versions)
        self.btn_start = QPushButton(tr("cyber.init_system"))
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 240, 255, 0.1);
                color: {COLORS['cyber_cyan']};
                border: 1px solid {COLORS['cyber_cyan']};
                padding: 4px 12px;
                font-weight: bold;
                font-family: 'Rajdhani';
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {COLORS['cyber_cyan']};
                color: black;
            }}
        """)
        self.btn_start.clicked.connect(self.start_camera_clicked.emit)
        layout.addWidget(self.btn_start)
        
        self.btn_add = QPushButton("+ CAM")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border_tech']};
                padding: 4px 8px;
            }}
             QPushButton:hover {{
                color: white;
                border-color: white;
            }}
        """)
        # We don't have a direct signal for this in MainWindow mapping yet, 
        # but let's connect to add_face for now or leave loose.
        # Ideally this should open Camera Selector. 
        # For now, let's just make it visually consistent.
        layout.addWidget(self.btn_add)
        
        return bar

    def _create_radar_widget(self):
        """Creates the bottom 'Radar' aesthetic widget."""
        box = QFrame()
        box.setFixedHeight(150)
        box.setStyleSheet(f"background: {COLORS['bg_void']}; border-top: 1px solid {COLORS['border_tech']};")
        
        layout = QVBoxLayout(box)
        
        self.radar_lbl = QLabel(tr("cyber.vector_search"))
        self.radar_lbl.setStyleSheet(f"color: {COLORS['cyber_cyan']}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        layout.addWidget(self.radar_lbl, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Placeholder for actual radar graphic (simulated with text for now)
        info = QLabel(
            "> SCANNING_SECTOR_7G\n"
            "> OBJECTS_TRACKED: 42\n"
            "> ANOMALY_INDEX: LOW"
        )
        info.setStyleSheet(f"color: {COLORS['text_muted']}; font-family: 'JetBrains Mono'; font-size: 9px;")
        layout.addWidget(info, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return box

    # --- API Methods for MainWindow compatibility ---
    
    def prepend_event(self, label, time_str, is_known, camera_name):
        """Adds a new event card to the top of the feed."""
        card = QFrame()
        if is_known:
            card.setProperty("class", "event_card_known")
            color = COLORS['acid_green']
            icon = "👤"
        else:
            card.setProperty("class", "event_card_alert")
            color = COLORS['alert_red']
            icon = "⚠️"
            
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.03);
                border-left: 3px solid {color};
                min-height: 50px;
            }}
            QFrame:hover {{ background-color: rgba(255, 255, 255, 0.06); }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        
        # Top Row: Name + Time
        top_row = QHBoxLayout()
        name_lbl = QLabel(f"{icon} {label}")
        name_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 13px;")
        
        time_lbl = QLabel(time_str)
        time_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-family: 'Consolas';")
        
        top_row.addWidget(name_lbl)
        top_row.addStretch()
        top_row.addWidget(time_lbl)
        layout.addLayout(top_row)
        
        # Bottom Row: Location/Camera
        loc_lbl = QLabel(f"LOC: {camera_name or 'CAM_01'}")
        loc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        layout.addWidget(loc_lbl)
        
        # Insert at top (index 0) of the feed layout
        # But wait, QVBoxLayout adds to bottom by default. 
        # To make it look like a "feed", newest should be at top.
        # We put addStretch() at the end of layout in _setup_ui.
        # usage: layout.insertWidget(0, widget)
        
        self.feed_layout.insertWidget(0, card)
        
        # Pruning handled by MainWindow calling takeItem? 
        # MainWindow expects QListWidget logic. Here we have a Layout.
        # We need to adapt MainWindow logic or implement 'count' and 'takeItem' here.

    def count(self):
        """Returns number of event cards."""
        return self.feed_layout.count() - 1 # Subtract stretch

    def takeItem(self, index):
        """Removes item at index (Compatible with ListWidget interface)."""
        # Note: Layout index includes spacer/stretch.
        item = self.feed_layout.itemAt(index)
        if item and item.widget():
            item.widget().deleteLater()
            
    def update_language(self):
        self.header_lbl.setText(tr("cyber.live_log"))
        self.radar_lbl.setText(tr("cyber.vector_search"))
        self.btn_start.setText(tr("cyber.init_system"))
