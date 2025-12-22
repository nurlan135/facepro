# Sprint 1: Kritik Problemlərin Həlli
> **Müddət:** 2 həftə  
> **Başlanğıc:** 2024-12-22  
> **Hədəf:** Multi-camera dəstəyi, YOLO tracking, passive enrollment

---

## 📋 Task Board

### ✅ Completed

#### PROD-001: Multi-Camera Dashboard İnteqrasiyası (5 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 1.1.1 | `CameraPage` + `VideoGrid` inteqrasiyası | | 1d | ✅ Artıq mövcud |
| 1.1.2 | `MainWindow._start_system()` refactoring | | 1d | ✅ Artıq mövcud |
| 1.1.3 | AIWorker strategiyası (shared vs parallel) | | 0.5d | ✅ Shared (implementasiya olunub) |
| 1.1.4 | Kamera seçimi UI yeniləmə | | 1d | ✅ Artıq mövcud |
| 1.1.5 | Aktiv kamera highlight | | 0.5d | ✅ Tamamlandı |
| 1.1.6 | Grid layout konfiqurasiyası | | 1d | ✅ Tamamlandı (1x1, 2x2, 3x3, 4x4) |

**Detallar:**

##### 1.1.1 CameraPage + VideoGrid İnteqrasiyası
```python
# Fayl: src/ui/dashboard/camera_page.py

# Dəyişiklik:
# - Mövcud tek VideoWidget əvəzinə VideoGrid istifadə et
# - cameras.json-dan bütün kameraları yüklə
# - Hər kamera üçün VideoWidget yarat

class CameraPage(QWidget):
    def __init__(self):
        self._video_grid = VideoGrid()  # Yeni
        self._setup_cameras()
    
    def _setup_cameras(self):
        cameras = load_cameras()  # config/cameras.json
        for cam_config in cameras:
            self._video_grid.add_camera_view(cam_config['name'])
```

##### 1.1.2 MainWindow._start_system() Refactoring
```python
# Fayl: src/ui/main_window.py

# Köhnə: Tek kamera, tek AIWorker
# Yeni: Çox kamera, AIWorker strategiyası

def _start_system(self):
    # Option A: Shared AIWorker (RAM efficient)
    self._ai_worker = AIWorker()
    
    for camera_name in self._camera_manager.camera_names:
        worker = self._camera_manager.get_camera(camera_name)
        worker.frame_ready.connect(
            lambda f, n=camera_name: self._ai_worker.process_frame(f, n)
        )
```

##### 1.1.3 AIWorker Strategiyası
| Strategiya | RAM | CPU/GPU | Latency | Tövsiyə |
|------------|-----|---------|---------|---------|
| Shared (1 AIWorker) | ✅ Az | ⚠️ Sequensial | ⚠️ Yüksək | 4GB RAM sistemlər |
| Parallel (N AIWorker) | ❌ Çox | ✅ Paralel | ✅ Aşağı | 8GB+ RAM, GPU |
| Hybrid (1 YOLO, N Face) | ✅ Orta | ✅ Yaxşı | ✅ Orta | **Optimal seçim** |

---

#### PROD-002: YOLO Tracking (3 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 1.2.1 | `ObjectDetector.detect()` → `track()` keçidi | | 0.5d | ✅ Artıq mövcud |
| 1.2.2 | Track ID → Detection mapping | | 0.5d | ✅ Artıq mövcud |
| 1.2.3 | Track persistency test | | 1d | ✅ Unit testlərdə |
| 1.2.4 | Multi-camera track ID namespacing | | 1d | ✅ Tamamlandı |

**Detallar:**

##### 1.2.1 YOLO Track Aktivləşdirmə
```python
# Fayl: src/core/object_detector.py

# Köhnə
results = self._model(frame)

# Yeni
results = self._model.track(
    frame, 
    persist=True,        # Track history saxla
    tracker="bytetrack"  # və ya "botsort"
)

# Track ID alma
for box in results[0].boxes:
    track_id = int(box.id) if box.id is not None else -1
```

##### 1.2.4 Multi-Camera Track ID Namespacing
```python
# Problem: Kamera1 track_id=5, Kamera2 track_id=5 -> konflikt

# Həll: Camera-specific prefix
def get_global_track_id(camera_index: int, local_track_id: int) -> int:
    return camera_index * 100000 + local_track_id
    
# Kamera 0, track 5 -> 5
# Kamera 1, track 5 -> 100005
# Kamera 2, track 5 -> 200005
```

---

#### PROD-003: Passive Enrollment Yenilənməsi (2 gün)

| # | Task | Assignee | Est. | Status |
|---|------|----------|------|--------|
| 1.3.1 | Time-based sampling implementasiyası | | 0.5d | ✅ Tamamlandı |
| 1.3.2 | Per-user sample counter | | 0.5d | ✅ Tamamlandı |
| 1.3.3 | Min/Max sample limitləri | | 0.5d | ✅ Tamamlandı |
| 1.3.4 | Settings inteqrasiyası | | 0.5d | ✅ Konstantlar əlavə edildi |

**Detallar:**

##### 1.3.1-4 Tam İmplementasiya
```python
# Fayl: src/core/services/recognition_service.py

class RecognitionService:
    # Yeni constants
    REID_SAMPLE_INTERVAL = 2.0       # saniyə
    REID_MIN_SAMPLES = 10
    REID_MAX_SAMPLES = 50
    
    def __init__(self, storage_worker):
        # Yeni tracking
        self._user_reid_samples: Dict[int, int] = {}      # user_id -> sample count
        self._user_last_sample: Dict[int, float] = {}     # user_id -> timestamp
    
    def _should_sample_reid(self, user_id: int) -> bool:
        now = time.time()
        
        # Max limitə çatdıqda sampling dayandır
        current_count = self._user_reid_samples.get(user_id, 0)
        if current_count >= self.REID_MAX_SAMPLES:
            return False
        
        # Time-based sampling
        last_sample = self._user_last_sample.get(user_id, 0)
        if now - last_sample < self.REID_SAMPLE_INTERVAL:
            return False
        
        return True
    
    def _passive_enrollment(self, frame, detection, user_id, name):
        if self._should_sample_reid(user_id):
            # ... existing logic ...
            
            # Update counters
            self._user_reid_samples[user_id] = self._user_reid_samples.get(user_id, 0) + 1
            self._user_last_sample[user_id] = time.time()
            
            logger.info(f"Re-ID sample {self._user_reid_samples[user_id]}/{self.REID_MAX_SAMPLES} for {name}")
```

---

## 🧪 Test Planı

### Unit Tests
```python
# tests/unit/test_multi_camera.py
def test_video_grid_add_camera():
    grid = VideoGrid()
    grid.add_camera_view("Cam1")
    grid.add_camera_view("Cam2")
    assert len(grid.camera_names) == 2

def test_track_id_namespacing():
    assert get_global_track_id(0, 5) == 5
    assert get_global_track_id(1, 5) == 100005
    assert get_global_track_id(2, 5) == 200005
```

### Integration Tests
```python
# tests/integration/test_multi_camera_flow.py
def test_four_camera_simultaneous():
    """4 kameranın eyni anda işləməsini test et"""
    pass

def test_track_persistence_across_frames():
    """Track ID-nin kadrar arası davam etməsini test et"""
    pass
```

### Manual Test Checklist
- [ ] 4 kamera əlavə et və eyni anda izlə
- [ ] Bir kameraya klik edib tam ekran aç
- [ ] Kamera bağlantısını kəs və reconnect-i izlə
- [ ] Gait recognition tracking ilə düzgün işləyir

---

## 📊 Sprint Burndown

| Gün | Planned | Completed | Remaining |
|-----|---------|-----------|-----------|
| 1 | 1.1.1 | | |
| 2 | 1.1.2 | | |
| 3 | 1.1.3, 1.2.1 | | |
| 4 | 1.1.4, 1.2.2 | | |
| 5 | 1.1.5, 1.2.3 | | |
| 6 | 1.1.6, 1.2.4 | | |
| 7 | 1.3.1, 1.3.2 | | |
| 8 | 1.3.3, 1.3.4 | | |
| 9-10 | Buffer / Testing | | |

---

## 🚧 Blocker-lar və Risklər

| Risk | Status | Mitigation |
|------|--------|------------|
| RAM overflow | 🔲 Monitor | Shared model loading |
| GPU bottleneck | 🔲 Monitor | CPU fallback |
| Track ID konflikt | 🔲 Həll olunmalı | Namespacing |

---

## ✅ Sprint Review Checklist

- [ ] Bütün tasklar tamamlandı
- [ ] Bütün testlər keçdi
- [ ] Code review tamamlandı
- [ ] Documentation yeniləndi
- [ ] Demo hazırdır
