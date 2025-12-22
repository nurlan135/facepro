"""
FacePro Telegram Notifier Module
Telegram bot vasitəsilə real-time bildiriş göndərmə.

Xüsusiyyətlər:
- Rate limiting (spam qoruması)
- Quiet hours (sakit saatlar)
- Batch notifications (toplu bildirişlər)
"""

import os
import io
import time
import threading
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, time as dt_time
from queue import Queue, Empty
from collections import deque
from threading import Lock

import requests
import numpy as np
import cv2

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import get_logger
from src.utils.helpers import load_config

logger = get_logger()


class TelegramNotifier:
    """
    Telegram Bot API vasitəsilə bildiriş göndərən modul.
    
    Xüsusiyyətlər:
    - Şəkilli bildirişlər
    - Rate limiting (spam qoruması)
    - Async göndərmə (ayrı thread)
    - Auto-retry mexanizmi
    """
    
    # Telegram API base URL
    API_BASE = "https://api.telegram.org/bot{token}/{method}"
    
    # Rate limiting defaults
    MIN_INTERVAL_SECONDS = 30  # Eyni şəxs üçün 30 saniyə fasilə
    GLOBAL_INTERVAL_SECONDS = 10  # İstənilən bildiriş arası minimum 10 saniyə
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # saniyə
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        """
        Args:
            bot_token: Telegram Bot Token (@BotFather-dən)
            chat_id: Bildiriş göndəriləcək chat ID
        """
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._enabled = bool(bot_token and chat_id)
        
        # Rate limiting
        self._last_notification_time: dict = {}  # {label: timestamp}
        self._last_any_notification = 0  # Son bildiriş vaxtı (global)
        
        # Enhanced rate limiting with deque
        self._message_times: deque = deque(maxlen=100)
        self._rate_lock = Lock()
        
        # Batch notification for unknown persons
        self._unknown_batch: List[Dict[str, Any]] = []
        self._batch_timer: Optional[threading.Timer] = None
        self._batch_lock = Lock()
        
        # Notification preferences
        self._notify_known_persons = False  # Tanınmış şəxslər üçün bildiriş göndərilsin?
        
        # Load notification config
        self._load_notification_config()
        
        # Async queue
        self._queue: Queue = Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Statistics
        self._sent_count = 0
        self._failed_count = 0
        
        if self._enabled:
            self._start_worker()
            logger.info("TelegramNotifier initialized and enabled")
        else:
            logger.info("TelegramNotifier initialized but disabled (no token/chat_id)")
    
    def _load_notification_config(self):
        """Load notification config from settings."""
        config = load_config()
        notif_config = config.get('notifications', {})
        
        self._max_per_minute = notif_config.get('max_per_minute', 10)
        self._batch_unknown = notif_config.get('batch_unknown', True)
        self._batch_interval = notif_config.get('batch_interval_seconds', 30)
        self._quiet_hours_enabled = notif_config.get('quiet_hours_enabled', False)
        self._quiet_start = self._parse_time(notif_config.get('quiet_hours_start', '23:00'))
        self._quiet_end = self._parse_time(notif_config.get('quiet_hours_end', '07:00'))
    
    def _parse_time(self, time_str: str) -> dt_time:
        """Parse HH:MM string to time object."""
        try:
            parts = time_str.split(':')
            return dt_time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return dt_time(0, 0)
    
    def _is_quiet_hours(self) -> bool:
        """Check if current time is within quiet hours."""
        if not self._quiet_hours_enabled:
            return False
        
        now = datetime.now().time()
        
        if self._quiet_start <= self._quiet_end:
            # Normal range (e.g., 09:00 - 17:00)
            return self._quiet_start <= now <= self._quiet_end
        else:
            # Overnight range (e.g., 23:00 - 07:00)
            return now >= self._quiet_start or now <= self._quiet_end
    
    def _check_rate_limit(self) -> bool:
        """Check if we can send a message (rate limiting)."""
        current = time.time()
        
        with self._rate_lock:
            # Remove messages older than 1 minute
            while self._message_times and current - self._message_times[0] > 60:
                self._message_times.popleft()
            
            if len(self._message_times) >= self._max_per_minute:
                logger.warning("Rate limit reached (max per minute)")
                return False
            
            self._message_times.append(current)
            return True
    
    @classmethod
    def from_config(cls) -> 'TelegramNotifier':
        """
        Config faylından settings yükləyərək instance yaradır.
        
        Returns:
            TelegramNotifier instance
        """
        config = load_config()
        telegram_config = config.get('telegram', {})
        
        return cls(
            bot_token=telegram_config.get('bot_token', ''),
            chat_id=telegram_config.get('chat_id', '')
        )
    
    def update_credentials(self, bot_token: str, chat_id: str):
        """
        Credentials-ləri yeniləyir.
        
        Args:
            bot_token: Yeni bot token
            chat_id: Yeni chat ID
        """
        self._bot_token = bot_token
        self._chat_id = chat_id
        was_enabled = self._enabled
        self._enabled = bool(bot_token and chat_id)
        
        if self._enabled and not was_enabled:
            self._start_worker()
            logger.info("TelegramNotifier enabled")
        elif not self._enabled and was_enabled:
            self._stop_worker()
            logger.info("TelegramNotifier disabled")
    
    def _start_worker(self):
        """Worker thread-i başladır."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Telegram worker thread started")
    
    def _stop_worker(self):
        """Worker thread-i dayandırır."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
            self._worker_thread = None
        logger.info("Telegram worker thread stopped")
    
    def _worker_loop(self):
        """Background worker loop."""
        while self._running:
            try:
                # Queue-dan mesaj al (timeout ilə)
                item = self._queue.get(timeout=1)
                
                if item is None:
                    continue
                
                message_type, data = item
                
                if message_type == 'photo':
                    self._send_photo_sync(**data)
                elif message_type == 'text':
                    self._send_message_sync(**data)
                    
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Telegram worker error: {e}")
    
    def _make_api_url(self, method: str) -> str:
        """API URL yaradır."""
        return self.API_BASE.format(token=self._bot_token, method=method)
    
    def _send_message_sync(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Sinxron mesaj göndərir.
        
        Args:
            text: Mesaj mətni
            parse_mode: Format (HTML, Markdown)
            
        Returns:
            Uğurlu olub-olmadığı
        """
        if not self._enabled:
            return False
        
        url = self._make_api_url("sendMessage")
        payload = {
            'chat_id': self._chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.post(url, data=payload, timeout=10)
                
                if response.status_code == 200:
                    self._sent_count += 1
                    logger.info(f"Telegram message sent successfully")
                    return True
                else:
                    logger.warning(f"Telegram API error: {response.status_code} - {response.text}")
                    
            except requests.RequestException as e:
                logger.error(f"Telegram request failed (attempt {attempt+1}): {e}")
                
            if attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY)
        
        self._failed_count += 1
        return False
    
    def _send_photo_sync(self, image: np.ndarray, caption: str = "") -> bool:
        """
        Sinxron şəkil göndərir.
        
        Args:
            image: BGR numpy array
            caption: Şəkil açıqlaması
            
        Returns:
            Uğurlu olub-olmadığı
        """
        if not self._enabled:
            return False
        
        url = self._make_api_url("sendPhoto")
        
        # OpenCV image -> JPEG bytes
        try:
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_bytes = io.BytesIO(buffer.tobytes())
            image_bytes.name = 'detection.jpg'
        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            return False
        
        payload = {
            'chat_id': self._chat_id,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        files = {'photo': image_bytes}
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Reset file pointer for retry
                image_bytes.seek(0)
                
                response = requests.post(url, data=payload, files=files, timeout=30)
                
                if response.status_code == 200:
                    self._sent_count += 1
                    logger.info(f"Telegram photo sent successfully")
                    return True
                else:
                    logger.warning(f"Telegram API error: {response.status_code} - {response.text}")
                    
            except requests.RequestException as e:
                logger.error(f"Telegram photo request failed (attempt {attempt+1}): {e}")
                
            if attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY)
        
        self._failed_count += 1
        return False
    
    def _should_send(self, label: str, is_known: bool = False) -> bool:
        """
        Rate limiting yoxlaması.
        
        Args:
            label: Bildiriş tipi/label-i
            is_known: Tanınmış şəxs olub-olmadığı
            
        Returns:
            Göndərilə biləcəyini
        """
        # Tanınmış şəxslər üçün bildiriş göndərilməsin (əgər seçilməyibsə)
        if is_known and not self._notify_known_persons:
            logger.debug(f"Skipped known person notification: {label}")
            return False
        
        current_time = time.time()
        
        # Global interval yoxlaması (bütün bildirişlər arası)
        if current_time - self._last_any_notification < self.GLOBAL_INTERVAL_SECONDS:
            return False
        
        # Eyni şəxs/label üçün interval
        last_time = self._last_notification_time.get(label, 0)
        if current_time - last_time < self.MIN_INTERVAL_SECONDS:
            return False
        
        self._last_notification_time[label] = current_time
        self._last_any_notification = current_time
        return True
    
    def send_detection_alert(
        self, 
        frame: np.ndarray, 
        label: str, 
        confidence: float,
        is_known: bool = False,
        camera_name: str = "Camera",
        priority: str = "NORMAL"
    ):
        """
        Detection alert-i göndərir (async).
        
        Args:
            frame: Detection frame-i (BGR)
            label: Aşkarlanan şəxs/obyekt adı
            confidence: Əminlik faizi
            is_known: Tanınmış şəxs olub-olmadığı
            camera_name: Kamera adı
            priority: Mesaj prioriteti ("NORMAL", "HIGH", "CRITICAL")
        """
        if not self._enabled:
            return
        
        # Quiet hours check (Critical messages bypass quiet hours)
        if self._is_quiet_hours() and priority != "CRITICAL":
            logger.debug("Notification skipped: quiet hours")
            return
        
        # Rate limit check (Global rate limit bypass for HIGH/CRITICAL)
        if priority == "NORMAL" and not self._check_rate_limit():
            return
        
        # Per-label rate limiting (Known persons or HIGH priority bypass per-label limit)
        if not is_known and priority == "NORMAL":
            if not self._should_send(f"{camera_name}:{label}", is_known):
                logger.debug(f"Rate limited: {label}")
                return
        
        # Batch unknown persons (Only NORMAL priority unknown persons are batched)
        if not is_known and self._batch_unknown and priority == "NORMAL":
            self._add_to_batch(frame, label, confidence, camera_name)
            return
        
        # Send immediately
        self._send_immediate_alert(frame, label, confidence, is_known, camera_name, priority)
    
    def _add_to_batch(self, frame: np.ndarray, label: str, confidence: float, camera_name: str):
        """Add unknown detection to batch."""
        with self._batch_lock:
            self._unknown_batch.append({
                'frame': frame.copy(),
                'label': label,
                'confidence': confidence,
                'camera': camera_name,
                'time': datetime.now()
            })
            
            # Start batch timer if not already running
            if self._batch_timer is None:
                self._batch_timer = threading.Timer(self._batch_interval, self._send_batch)
                self._batch_timer.daemon = True
                self._batch_timer.start()
    
    def _send_batch(self):
        """Send batched unknown detections."""
        with self._batch_lock:
            self._batch_timer = None
            
            if not self._unknown_batch:
                return
            
            count = len(self._unknown_batch)
            cameras = set(d['camera'] for d in self._unknown_batch)
            
            # Create summary message
            message = f"🔔 <b>{count} naməlum şəxs aşkarlandı</b>\n\n"
            message += f"📷 Kameralar: {', '.join(cameras)}\n"
            message += f"⏰ Son {self._batch_interval} saniyə ərzində"
            
            # Use the most recent frame
            latest = self._unknown_batch[-1]
            
            self._queue.put(('photo', {
                'image': latest['frame'],
                'caption': message
            }))
            
            self._unknown_batch.clear()
            logger.info(f"Batch notification sent: {count} detections")
    
    def _send_immediate_alert(
        self, 
        frame: np.ndarray, 
        label: str, 
        confidence: float,
        is_known: bool,
        camera_name: str,
        priority: str = "NORMAL"
    ):
        """Send immediate alert (not batched)."""
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        # Status emoji
        if is_known:
            status = "✅ Tanınmış şəxs"
            emoji = "👤"
        elif priority == "CRITICAL":
            status = "🚨 TƏHLÜKƏ!"
            emoji = "🆘"
        else:
            status = "⚠️ Naməlum şəxs"
            emoji = "🚨"
        
        # Priority prefix
        prio_prefix = f" [{priority}]" if priority != "NORMAL" else ""
        
        # Caption formatı
        caption = (
            f"{emoji} <b>FacePro Alert</b>{prio_prefix}\n\n"
            f"📷 <b>Kamera:</b> {camera_name}\n"
            f"👤 <b>Şəxs:</b> {label}\n"
            f"📊 <b>Əminlik:</b> {confidence:.0%}\n"
            f"🔒 <b>Status:</b> {status}\n"
            f"🕐 <b>Vaxt:</b> {timestamp}"
        )
        
        # Queue-ya əlavə et
        self._queue.put(('photo', {
            'image': frame.copy(),
            'caption': caption
        }))
        
        logger.info(f"Detection alert queued: {label}")
    
    def send_system_message(self, message: str, level: str = "info"):
        """
        Sistem mesajı göndərir (async).
        
        Args:
            message: Mesaj mətni
            level: Səviyyə (info, warning, error)
        """
        if not self._enabled:
            return
        
        # Emoji seçimi
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '🚫',
            'success': '✅'
        }
        emoji = emoji_map.get(level, 'ℹ️')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        formatted = f"{emoji} <b>FacePro</b> [{timestamp}]\n{message}"
        
        self._queue.put(('text', {'text': formatted}))
    
    def send_startup_message(self):
        """Sistem başladığını bildirir."""
        self.send_system_message(
            "🟢 FacePro aktiv və izləyir...\n\n"
            "Həm tanınmış, həm də naməlum şəxslər aşkarlandığında bildiriş alacaqsınız.",
            level="success"
        )
    
    def send_shutdown_message(self):
        """Sistem dayandığını bildirir."""
        self.send_system_message(
            "🔴 FacePro dayandırıldı.",
            level="warning"
        )
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Telegram bağlantısını test edir.
        
        Returns:
            (uğurlu, mesaj)
        """
        if not self._bot_token or not self._chat_id:
            return False, "Bot token və ya Chat ID boşdur"
        
        try:
            # getMe ilə bot-u yoxla
            url = self._make_api_url("getMe")
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return False, f"Bot token səhvdir: {response.status_code}"
            
            bot_info = response.json().get('result', {})
            bot_name = bot_info.get('first_name', 'Bot')
            
            # Test mesajı göndər
            test_url = self._make_api_url("sendMessage")
            test_payload = {
                'chat_id': self._chat_id,
                'text': f"✅ Test uğurlu!\n\n🤖 Bot: {bot_name}\n📱 FacePro ilə əlaqə quruldu.",
                'parse_mode': 'HTML'
            }
            
            test_response = requests.post(test_url, data=test_payload, timeout=10)
            
            if test_response.status_code == 200:
                return True, f"Bağlantı uğurlu! Bot: {bot_name}"
            else:
                error = test_response.json().get('description', 'Unknown error')
                return False, f"Chat ID səhvdir: {error}"
                
        except requests.RequestException as e:
            return False, f"Şəbəkə xətası: {str(e)}"
    
    @property
    def is_enabled(self) -> bool:
        """Notifier aktiv olub-olmadığı."""
        return self._enabled
    
    @property
    def stats(self) -> dict:
        """Statistika."""
        return {
            'sent': self._sent_count,
            'failed': self._failed_count,
            'queue_size': self._queue.qsize()
        }
    
    def stop(self):
        """Notifier-i dayandırır."""
        self._stop_worker()
        logger.info("TelegramNotifier stopped")


# Singleton instance
_notifier_instance: Optional[TelegramNotifier] = None

def get_telegram_notifier() -> TelegramNotifier:
    """
    Singleton TelegramNotifier instance qaytarır.
    
    Returns:
        TelegramNotifier instance
    """
    global _notifier_instance
    
    if _notifier_instance is None:
        _notifier_instance = TelegramNotifier.from_config()
    
    return _notifier_instance


if __name__ == "__main__":
    # Test
    print("Testing TelegramNotifier...")
    
    # Manual test (token/chat_id daxil edin)
    notifier = TelegramNotifier(
        bot_token="",  # TOKEN DAXIL ET
        chat_id=""     # CHAT ID DAXIL ET
    )
    
    if notifier.is_enabled:
        success, message = notifier.test_connection()
        print(f"Connection test: {success} - {message}")
    else:
        print("Notifier disabled - token/chat_id boşdur")
    
    print("Test complete")
