"""
FacePro Performance Monitor Widget
Displays real-time system and AI processing statistics.
"""

import time
import os
from collections import deque
from typing import Optional

import psutil
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont

from src.utils.logger import get_logger

logger = get_logger()

class PerformanceMonitor(QFrame):
    """Real-time performance monitoring widget with visual indicators"""
    
    performance_alert = pyqtSignal(str, str)  # metric_name, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("performanceMonitor")
        self.setStyleSheet("""
            #performanceMonitor {
                background-color: rgba(30, 30, 30, 180);
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: #ccc;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
            .metricValue {
                color: #00ff00;
                font-weight: bold;
            }
            .metricAlert {
                color: #ff3333;
            }
        """)
        
        # History & Stats
        self._fps_history = deque(maxlen=30)
        self._proc_history = deque(maxlen=30)
        self._last_frame_time = time.time()
        
        # Thresholds
        self._fps_threshold = 10.0
        self._mem_threshold_percent = 85.0
        
        self._setup_ui()
        
        # Update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_stats)
        self.timer.start(2000) # Update system stats every 2 seconds
        
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Stats Labels
        # FPS
        layout.addWidget(QLabel("FPS:"), 0, 0)
        self.lbl_fps = QLabel("--")
        self.lbl_fps.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_fps.setProperty("class", "metricValue")
        layout.addWidget(self.lbl_fps, 0, 1)
        
        # Processing time
        layout.addWidget(QLabel("AI Proc:"), 1, 0)
        self.lbl_proc = QLabel("-- ms")
        self.lbl_proc.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_proc.setProperty("class", "metricValue")
        layout.addWidget(self.lbl_proc, 1, 1)
        
        # CPU
        layout.addWidget(QLabel("CPU:"), 2, 0)
        self.lbl_cpu = QLabel("--%")
        self.lbl_cpu.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_cpu.setProperty("class", "metricValue")
        layout.addWidget(self.lbl_cpu, 2, 1)
        
        # RAM
        layout.addWidget(QLabel("RAM:"), 3, 0)
        self.lbl_ram = QLabel("-- MB")
        self.lbl_ram.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_ram.setProperty("class", "metricValue")
        layout.addWidget(self.lbl_ram, 3, 1)
        
        # GPU (Optional)
        layout.addWidget(QLabel("GPU:"), 4, 0)
        self.lbl_gpu = QLabel("N/A")
        self.lbl_gpu.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_gpu.setProperty("class", "metricValue")
        layout.addWidget(self.lbl_gpu, 4, 1)

    def update_fps(self):
        """Should be called whenever a frame is rendered"""
        now = time.time()
        dt = now - self._last_frame_time
        self._last_frame_time = now
        
        if dt > 0:
            current_fps = 1.0 / dt
            self._fps_history.append(current_fps)
            avg_fps = sum(self._fps_history) / len(self._fps_history)
            
            self.lbl_fps.setText(f"{avg_fps:.1f}")
            
            # Color coding
            if avg_fps < self._fps_threshold:
                self.lbl_fps.setStyleSheet("color: #ff3333;")
            elif avg_fps < 20:
                self.lbl_fps.setStyleSheet("color: #ffaa00;")
            else:
                self.lbl_fps.setStyleSheet("color: #00ff00;")

    def update_ai_time(self, ms: float):
        """Update AI processing time metric"""
        self._proc_history.append(ms)
        avg_proc = sum(self._proc_history) / len(self._proc_history)
        self.lbl_proc.setText(f"{avg_proc:.0f} ms")
        
        if avg_proc > 200:
            self.lbl_proc.setStyleSheet("color: #ffaa00;")
        else:
            self.lbl_proc.setStyleSheet("color: #00ff00;")

    def _update_stats(self):
        """Update system-wide resource usage"""
        try:
            # CPU
            cpu_usage = psutil.cpu_percent()
            self.lbl_cpu.setText(f"{cpu_usage}%")
            
            # RAM
            mem = psutil.virtual_memory()
            mem_usage_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            self.lbl_ram.setText(f"{mem_usage_mb:.0f} MB")
            
            if mem.percent > self._mem_threshold_percent:
                self.lbl_ram.setStyleSheet("color: #ff3333;")
                self.performance_alert.emit("RAM", f"High memory usage: {mem.percent}%")
            else:
                self.lbl_ram.setStyleSheet("color: #00ff00;")
                
            # GPU
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    self.lbl_gpu.setText(f"{gpu.load*100:.0f}% ({gpu.memoryUsed}MB)")
                else:
                    self.lbl_gpu.setText("N/A")
            except:
                self.lbl_gpu.setText("N/A")
                
        except Exception as e:
            logger.error(f"Error updating performance stats: {e}")
