"""
FacePro Camera Thread Module
RTSP/Webcam video capture üçün QThread.
Auto-reconnect funksionallığı ilə.
"""

import time
from typing import Optional
from dataclasses import dataclass

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# FFMPEG h264 xəta mesajlarını gizlət
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"  # AV_LOG_QUIET

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class CameraConfig:
    """Kamera konfiqurasiyası."""
    source: str  # RTSP URL və ya webcam index (0, 1, ...)
    name: str = "Camera"
    target_fps: int = 30
    reconnect_interval: int = 5  # saniyə
    timeout: int = 10  # saniyə
    roi_points: Optional[list] = None  # [(x,y), ...] normalized 0-1


class CameraWorker(QThread):
    """
    Video capture üçün QThread.
    
    Signals:
        frame_ready: Yeni frame hazır olduqda (frame, camera_name)
        connection_status: Bağlantı statusu dəyişdikdə (is_connected, camera_name)
        error_occurred: Xəta baş verdikdə (error_message, camera_name)
    """
    
    frame_ready = pyqtSignal(np.ndarray, str)
    connection_status = pyqtSignal(bool, str)
    error_occurred = pyqtSignal(str, str)
    
    def __init__(self, config: CameraConfig, parent=None):
        """
        Args:
            config: Kamera konfiqurasiyası
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self.config = config
        self._running = False
        self._paused = False
        self._mutex = QMutex()
        
        self._cap: Optional[cv2.VideoCapture] = None
        self._frame_interval = 1.0 / config.target_fps
        self._last_frame_time = 0
        self._consecutive_failures = 0
        self._max_failures = 100  # 100 ardıcıl uğursuzluqdan sonra reconnect (h264 xətalarına dözümlü)
        
        logger.info(f"CameraWorker created: {config.name} -> {config.source}")
    
    @property
    def is_connected(self) -> bool:
        """Kamera bağlıdırmı?"""
        return self._cap is not None and self._cap.isOpened()
    
    def run(self):
        """Thread-in əsas döngüsü."""
        self._running = True
        self._last_valid_frame = None
        logger.info(f"Camera thread started: {self.config.name}")
        
        while self._running:
            # Paused vəziyyəti
            if self._paused:
                time.sleep(0.1)
                continue
            
            # Bağlantı yoxdursa, qoşul
            if not self.is_connected:
                self._connect()
                continue
            
            # Frame oxu
            try:
                current_time = time.time()
                
                # FPS limitləmə
                if current_time - self._last_frame_time < self._frame_interval:
                    time.sleep(0.001)
                    continue
                
                ret, frame = self._cap.read()
                
                if ret and frame is not None and frame.size > 0:
                    # Frame-in valid olduğunu yoxla (tamamilə qara və ya boz deyil)
                    # Hikvision bəzən corrupt frame-lər göndərir
                    if self._is_valid_frame(frame):
                        self._consecutive_failures = 0
                        self._last_frame_time = current_time
                        self._last_valid_frame = frame.copy()
                        self.frame_ready.emit(frame, self.config.name)
                    else:
                        # Corrupt frame - son valid frame-i istifadə et
                        self._consecutive_failures += 1
                        if self._last_valid_frame is not None and self._consecutive_failures < 10:
                            self.frame_ready.emit(self._last_valid_frame, self.config.name)
                else:
                    self._handle_read_failure()
                    
            except Exception as e:
                logger.error(f"Frame read error: {e}")
                self._handle_read_failure()
        
        # Thread bitdikdə bağlantını bağla
        self._disconnect()
        logger.info(f"Camera thread stopped: {self.config.name}")
    
    def _is_valid_frame(self, frame: np.ndarray) -> bool:
        """
        Frame-in valid olduğunu yoxlayır.
        Corrupt və ya boş frame-ləri aşkarlayır.
        """
        if frame is None or frame.size == 0:
            return False
        
        # Frame ölçüsü çox kiçikdirsə
        if frame.shape[0] < 100 or frame.shape[1] < 100:
            return False
        
        # Tamamilə eyni rəngdirsə (qara, boz, yaşıl)
        # Standart sapma çox aşağıdırsa, frame corrupt ola bilər
        try:
            std = np.std(frame)
            if std < 5:  # Demək olar ki, eyni rəng
                return False
        except:
            return False
        
        return True
    
    def _connect(self):
        """Kameraya qoşulmağa cəhd edir."""
        logger.info(f"Connecting to camera: {self.config.source}")
        self.connection_status.emit(False, self.config.name)
        
        try:
            # Source tip yoxlaması (webcam vs RTSP)
            if isinstance(self.config.source, int) or self.config.source.isdigit():
                source = int(self.config.source)
                is_network_stream = False
            else:
                source = self.config.source
                is_network_stream = source.startswith('rtsp') or source.startswith('http')
            
            # RTSP/HTTP stream üçün FFmpeg parametrlərini ayarla
            if is_network_stream:
                # Hikvision DVR üçün optimallaşdırılmış parametrlər
                os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
                    "rtsp_transport;tcp|"
                    "buffer_size;1024000|"
                    "max_delay;500000|"
                    "stimeout;5000000|"
                    "reorder_queue_size;0|"
                    "fflags;discardcorrupt+nobuffer"
                )
            
            # VideoCapture yaratmaq
            if is_network_stream:
                # Əvvəlcə FFMPEG backend ilə cəhd et
                self._cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                
                # Əgər açılmadısa, default backend ilə cəhd et
                if not self._cap.isOpened():
                    logger.warning(f"FFMPEG backend failed, trying default: {self.config.name}")
                    self._cap = cv2.VideoCapture(source)
            else:
                self._cap = cv2.VideoCapture(source)
            
            # RTSP/HTTP üçün timeout ayarla
            if is_network_stream:
                self._cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.config.timeout * 1000)
                self._cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.config.timeout * 1000)
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            
            if self._cap.isOpened():
                # Stream stabilization - wait for first valid frame with timeout
                # PERFORMANCE: Don't wait fixed N frames, just get first valid one
                warmup_start = time.time()
                max_warmup_time = 2.0 if is_network_stream else 0.5  # seconds
                valid_frame_count = 0
                
                while time.time() - warmup_start < max_warmup_time:
                    ret, frame = self._cap.read()
                    if ret and frame is not None and frame.size > 0:
                        valid_frame_count += 1
                        if valid_frame_count >= 3:  # At least 3 valid frames
                            break
                    time.sleep(0.05)  # 50ms between attempts
                
                logger.info(f"Warmup: {valid_frame_count} valid frames in {time.time() - warmup_start:.2f}s")
                
                # Kamera parametrlərini oxu
                width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(self._cap.get(cv2.CAP_PROP_FPS)) or self.config.target_fps
                
                if width > 0 and height > 0:
                    logger.info(f"Camera connected: {self.config.name} ({width}x{height} @ {fps}fps)")
                    self.connection_status.emit(True, self.config.name)
                    self._consecutive_failures = 0
                else:
                    raise Exception(f"Invalid resolution: {width}x{height}")
            else:
                raise Exception("Failed to open video capture")
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.error_occurred.emit(str(e), self.config.name)
            if self._cap is not None:
                try:
                    self._cap.release()
                except:
                    pass
            self._cap = None
            
            # Reconnect intervalı gözlə
            if self._running:
                time.sleep(self.config.reconnect_interval)
    
    def _disconnect(self):
        """Kamera bağlantısını bağlayır."""
        if self._cap is not None:
            try:
                self._cap.release()
            except:
                pass
            self._cap = None
            logger.info(f"Camera disconnected: {self.config.name}")
            self.connection_status.emit(False, self.config.name)
    
    def _handle_read_failure(self):
        """Frame oxuma uğursuzluğunu idarə edir."""
        self._consecutive_failures += 1
        
        if self._consecutive_failures >= self._max_failures:
            logger.warning(f"Too many failures, reconnecting: {self.config.name}")
            self._disconnect()
            time.sleep(self.config.reconnect_interval)
            self._consecutive_failures = 0
    
    def stop(self):
        """Thread-i dayandırır."""
        logger.info(f"Stopping camera thread: {self.config.name}")
        self._running = False
        self.wait(5000)  # 5 saniyə gözlə
    
    def pause(self):
        """Thread-i pauzaya alır."""
        with QMutexLocker(self._mutex):
            self._paused = True
        logger.debug(f"Camera paused: {self.config.name}")
    
    def resume(self):
        """Thread-i davam etdirir."""
        with QMutexLocker(self._mutex):
            self._paused = False
        logger.debug(f"Camera resumed: {self.config.name}")
    
    def take_snapshot(self) -> Optional[np.ndarray]:
        """
        Cari frame-in surətini qaytarır.
        
        Returns:
            Frame və ya None
        """
        if not self.is_connected:
            return None
        
        try:
            ret, frame = self._cap.read()
            return frame if ret else None
        except:
            return None


class CameraManager:
    """
    Birdən çox kameranı idarə edən sinif.
    """
    
    def __init__(self):
        self._cameras: dict[str, CameraWorker] = {}
        logger.info("CameraManager initialized")
    
    def add_camera(self, config: CameraConfig) -> CameraWorker:
        """
        Yeni kamera əlavə edir.
        
        Args:
            config: Kamera konfiqurasiyası
            
        Returns:
            CameraWorker instance
        """
        if config.name in self._cameras:
            logger.warning(f"Camera already exists: {config.name}")
            return self._cameras[config.name]
        
        worker = CameraWorker(config)
        self._cameras[config.name] = worker
        return worker
    
    def remove_camera(self, name: str):
        """Kameranı silir."""
        if name in self._cameras:
            self._cameras[name].stop()
            del self._cameras[name]
            logger.info(f"Camera removed: {name}")
    
    def get_camera(self, name: str) -> Optional[CameraWorker]:
        """Kameranı qaytarır."""
        return self._cameras.get(name)
    
    def start_all(self):
        """Bütün kameraları başladır."""
        for worker in self._cameras.values():
            if not worker.isRunning():
                worker.start()
    
    def stop_all(self):
        """Bütün kameraları dayandırır."""
        for worker in self._cameras.values():
            worker.stop()
    
    @property
    def camera_names(self) -> list:
        """Kamera adlarının siyahısı."""
        return list(self._cameras.keys())


if __name__ == "__main__":
    # Test (webcam)
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    config = CameraConfig(source="0", name="Webcam", target_fps=15)
    worker = CameraWorker(config)
    
    frame_count = [0]
    
    def on_frame(frame, name):
        frame_count[0] += 1
        if frame_count[0] % 30 == 0:
            print(f"Received {frame_count[0]} frames from {name}")
        if frame_count[0] >= 60:
            worker.stop()
            app.quit()
    
    def on_status(connected, name):
        print(f"Camera {name}: {'Connected' if connected else 'Disconnected'}")
    
    worker.frame_ready.connect(on_frame)
    worker.connection_status.connect(on_status)
    worker.start()
    
    sys.exit(app.exec())
