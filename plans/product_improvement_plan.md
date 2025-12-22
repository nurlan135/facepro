# FacePro Məhsul Təkmilləşdirmə Planı
> **Yaradılma tarixi:** 2025-12-22  
> **Hazırlayan:** Product Manager Analysis  
> **Versiya:** 1.0

---

## 📋 İcmal

Bu sənəd FacePro layihəsinin kod analizindən əldə edilən problemləri və onların həlli üçün detallı planı əhatə edir.

### Prioritet Səviyyələri
| Səviyyə | Təsvir | SLA |
|---------|--------|-----|
| 🔴 P0 - Kritik | Məhsulun əsas funksionallığına təsir edir | 1-2 Sprint |
| 🟠 P1 - Yüksək | İstifadəçi təcrübəsinə ciddi təsir edir | 2-3 Sprint |
| 🟡 P2 - Orta | Keyfiyyət və dəstək yükünə təsir edir | 3-4 Sprint |
| 🔵 P3 - Aşağı | Nice-to-have, gələcək versiya üçün | Backlog |

---

## 🔴 Sprint 1: Kritik Problemlərin Həlli (2 həftə)

### 1.1 Multi-Camera Dashboard İnteqrasiyası
**Problem ID:** PROD-001  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 5 gün  

#### Təsvir
Hal-hazırda `VideoGrid` komponenti mövcuddur, lakin `MainWindow` yalnız bir kamera ilə işləyir. Dashboard-da birdən çox kameranın eyni anda izlənməsi mümkün deyil.

#### Təsirlənən Fayllar
- `src/ui/main_window.py`
- `src/ui/video_widget.py`
- `src/ui/dashboard/camera_page.py`

#### Tapşırıqlar
- [ ] **1.1.1** `CameraPage` komponentini `VideoGrid` ilə inteqrasiya et
- [ ] **1.1.2** `MainWindow._start_system()` funksiyasını çox kamera dəstəkləyəcək şəkildə refactor et
- [ ] **1.1.3** Hər kamera üçün ayrı `AIWorker` instance yaratma strategiyasını müəyyənləşdir
  - **Variant A:** Hər kamera üçün ayrı AIWorker (paralel processing)
  - **Variant B:** Bir AIWorker, round-robin frame processing
- [ ] **1.1.4** Kamera seçimi UI-ı yenilə (grid-dən kamera seçmək)
- [ ] **1.1.5** Aktiv kamera vurğulanması (border highlight)
- [ ] **1.1.6** Grid layout konfiqurasiyası (2x2, 3x3, 4x4)

#### Qəbul Kriteriyaları
- [ ] 4 kamera eyni anda izlənə bilər
- [ ] Hər kamerada ayrıca detection göstərilir
- [ ] Kameraya klik etdikdə tam ekran görünüşə keçir
- [ ] FPS 10+ qalır (4 kamera ilə)

#### Risklər
| Risk | Ehtimal | Təsir | Azaltma |
|------|---------|-------|---------|
| RAM overflow (4 AIWorker) | Orta | Yüksək | Shared model loading |
| GPU bottleneck | Yüksək | Orta | CPU fallback strategiyası |

---

### 1.2 YOLO Tracking İnteqrasiyası
**Problem ID:** PROD-002  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 3 gün  

#### Təsvir
Gait recognition `track_id`-yə əsaslanır, lakin YOLO-nun ByteTrack/BoT-SORT tracking-i tam aktivləşdirilməyib.

#### Təsirlənən Fayllar
- `src/core/object_detector.py`
- `src/core/services/detection_service.py`
- `src/core/services/recognition_service.py`

#### Tapşırıqlar
- [ ] **1.2.1** `ObjectDetector` class-ında `model.track()` metodunu aktivləşdir
- [ ] **1.2.2** Track ID-ləri `Detection` obyektinə düzgün ötür
- [ ] **1.2.3** Track ID persistentliyini test et (eyni şəxs, eyni ID)
- [ ] **1.2.4** Multi-kamera halında track ID konfliktini həll et

#### Qəbul Kriteriyaları
- [ ] Eyni şəxs kadr arasında eyni `track_id` saxlayır
- [ ] Track pozulduqda (occlusion) yenidən assign olunur
- [ ] Gait recognition doğru track_id ilə işləyir

---

### 1.3 Passive Enrollment Strategiyasının Yenilənməsi
**Problem ID:** PROD-003  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 2 gün  

#### Təsvir
Random sampling (`np.random.random() < 0.05`) etibarsızdır. Bəzi şəxslər üçün Re-ID data heç vaxt toplanmaya bilər.

#### Təsirlənən Fayllar
- `src/core/services/recognition_service.py`

#### Tapşırıqlar
- [ ] **1.3.1** Time-based sampling strategiyasına keç (hər 2 saniyədə 1 sample)
- [ ] **1.3.2** Per-user sample counter əlavə et
- [ ] **1.3.3** Minimum sample sayına çatana qədər sampling davam etsin
- [ ] **1.3.4** Maximum sample limitini konfiqurasiya oluna bilən et

#### Kod Dəyişikliyi Nümunəsi
```python
# Köhnə
if np.random.random() < 0.05:
    # sample

# Yeni  
SAMPLE_INTERVAL_SECONDS = 2.0
MIN_SAMPLES_PER_USER = 10
MAX_SAMPLES_PER_USER = 50

if self._should_sample_reid(user_id, current_time):
    # sample
```

#### Qəbul Kriteriyaları
- [ ] Hər tanınmış şəxs üçün minimum 10 Re-ID embedding toplanır
- [ ] Sampling predictable intervallarla baş verir
- [ ] Sample limitinə çatdıqda sampling dayanır

---

## 🟠 Sprint 2: Test Coverage və Error Handling (2 həftə)

### 2.1 Unit Test Coverage Artırılması
**Problem ID:** PROD-004  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 5 gün  
**Hədəf Coverage:** 60%  

#### Təsirlənən Fayllar
- `tests/` qovluğu (yeni fayllar)

#### Tapşırıqlar
- [ ] **2.1.1** `pytest-cov` konfiqurasiyası
- [ ] **2.1.2** Core modullar üçün unit testlər:
  - [ ] `test_face_recognizer.py`
  - [ ] `test_reid_engine.py`
  - [ ] `test_detection_service.py`
  - [ ] `test_recognition_service.py`
  - [ ] `test_storage_worker.py`
  - [ ] `test_camera_thread.py`
- [ ] **2.1.3** Database repository testləri:
  - [ ] `test_user_repository.py`
  - [ ] `test_embedding_repository.py`
  - [ ] `test_event_repository.py`
- [ ] **2.1.4** Utils testləri:
  - [ ] `test_license_manager.py`
  - [ ] `test_i18n.py`
  - [ ] `test_helpers.py`
- [ ] **2.1.5** CI/CD pipeline əlavə et (GitHub Actions)

#### Test Strategiyası
```
tests/
├── unit/
│   ├── core/
│   │   ├── test_face_recognizer.py
│   │   ├── test_reid_engine.py
│   │   └── ...
│   ├── database/
│   │   └── ...
│   └── utils/
│       └── ...
├── integration/
│   ├── test_ai_pipeline.py
│   └── test_camera_flow.py
└── conftest.py  # Fixtures
```

#### Qəbul Kriteriyaları
- [ ] Coverage >= 60%
- [ ] Bütün testlər CI-da keçir
- [ ] Kritik funksiyalar (authentication, face recognition) 80%+ coverage

---

### 2.2 User-Facing Error Handling
**Problem ID:** PROD-005  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 3 gün  

#### Təsvir
Xətalar yalnız log olunur, istifadəçiyə göstərilmir. Bu, "silent failure" problemlərinə səbəb olur.

#### Təsirlənən Fayllar
- `src/ui/main_window.py`
- `src/core/ai_thread.py`
- `src/core/camera_thread.py`
- `src/ui/dashboard/logs_page.py`

#### Tapşırıqlar
- [ ] **2.2.1** `ErrorNotificationService` singleton yaratmaq
- [ ] **2.2.2** Critical error-lar üçün toast notification sistemi
- [ ] **2.2.3** Kamera connection error-larını status bar-da göstərmək
- [ ] **2.2.4** AI processing error-ları üçün visual feedback
- [ ] **2.2.5** Error history logs page-də göstərilsin

#### UI Nümunəsi
```
┌─────────────────────────────────────┐
│ ⚠️ Kamera "Giriş" əlaqəsi kəsildi   │
│    Yenidən qoşulmağa çalışılır...   │
│    [3/5 cəhd]                       │
└─────────────────────────────────────┘
```

#### Qəbul Kriteriyaları
- [ ] Kamera xətaları istifadəçiyə göstərilir
- [ ] Disk dolu xətası bildiriş kimi verilir
- [ ] AI model yüklənmə xətası izah edilir

---

### 2.3 Kamera Reconnect UX Təkmilləşdirmələri
**Problem ID:** PROD-006  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 2 gün  

#### Tapşırıqlar
- [ ] **2.3.1** Reconnect counter UI-da göstərilsin
- [ ] **2.3.2** Reconnect interval konfiqurasiya oluna bilən olsun (Settings)
- [ ] **2.3.3** Maximum cəhd sayından sonra "Manual Reconnect" düyməsi
- [ ] **2.3.4** Kamera status ikonları (🟢 Connected, 🟡 Reconnecting, 🔴 Failed)

---

## 🟡 Sprint 3: Konfiqurasiya və i18n (2 həftə)

### 3.1 i18n Refactoring
**Problem ID:** PROD-007  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 4 gün  

#### Təsvir
Bütün tərcümələr 975 sətirlik bir Python faylındadır. Bu, dəstəklənməsi çətin strukturdur.

#### Tapşırıqlar
- [ ] **3.1.1** `locales/` qovluğu yaratmaq
- [ ] **3.1.2** JSON formatında ayrı fayllara bölmək:
  - `locales/en.json`
  - `locales/az.json`
  - `locales/ru.json` (gələcək)
- [ ] **3.1.3** `I18nManager` class-ını JSON loader ilə yeniləmək
- [ ] **3.1.4** Missing key fallback mexanizmi
- [ ] **3.1.5** Translation validation script (missing keys aşkarlaması)

#### Yeni Struktur
```
locales/
├── en.json
├── az.json
└── _schema.json  # Key validation schema
```

#### Qəbul Kriteriyaları
- [ ] Tərcümələr JSON formatında saxlanılır
- [ ] Yeni dil əlavə etmək sadədir (yeni JSON fayl)
- [ ] Missing translation key-lər log olunur

---

### 3.2 Konfiqurasiya Validation
**Problem ID:** PROD-008  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 2 gün  

#### Tapşırıqlar
- [ ] **3.2.1** `pydantic` və ya manual validation əlavə et
- [ ] **3.2.2** Settings yükləndikdə validation
- [ ] **3.2.3** Invalid dəyərlər üçün default fallback
- [ ] **3.2.4** Settings UI-da input validation (min/max, format)

#### Validation Nümunəsi
```python
class AISettings(BaseModel):
    motion_threshold: int = Field(ge=0, le=100, default=25)
    face_confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.6)
    reid_confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.75)
```

---

### 3.3 Notification Throttling Yenilənməsi
**Problem ID:** PROD-009  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 2 gün  

#### Tapşırıqlar
- [ ] **3.3.1** Global rate limit əlavə et (per-minute cap)
- [ ] **3.3.2** Batch notification support (5 unknown -> 1 mesaj)
- [ ] **3.3.3** Quiet hours konfiqurasiyası
- [ ] **3.3.4** Notification priority levels

#### Konfiqurasiya
```json
{
  "notifications": {
    "max_per_minute": 10,
    "batch_unknown": true,
    "batch_interval_seconds": 30,
    "quiet_hours": {
      "enabled": false,
      "start": "23:00",
      "end": "07:00"
    }
  }
}
```

---

## 🔵 Sprint 4: Database və Backup (2 həftə)

### 4.1 Database Migration System
**Problem ID:** PROD-010  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 4 gün  

#### Tapşırıqlar
- [ ] **4.1.1** `migrations/` qovluğu yaratmaq
- [ ] **4.1.2** Schema versioning table (`schema_version`)
- [ ] **4.1.3** Migration runner utility
- [ ] **4.1.4** Rollback support
- [ ] **4.1.5** Auto-migration on startup

#### Migration Strukturu
```
migrations/
├── 001_initial_schema.sql
├── 002_add_gait_embeddings.sql
├── 003_add_insightface_columns.sql
└── runner.py
```

---

### 4.2 Export/Backup Funksionallığı
**Problem ID:** PROD-011  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 3 gün  

#### Tapşırıqlar
- [ ] **4.2.1** Database backup (SQLite copy)
- [ ] **4.2.2** Faces export (ZIP archive)
- [ ] **4.2.3** Settings export (JSON)
- [ ] **4.2.4** Full backup wizard UI
- [ ] **4.2.5** Restore functionality

---

### 4.3 Performance Monitoring Dashboard
**Problem ID:** PROD-012  
**Status:** 🔲 Başlanmayıb  
**Təxmini Vaxt:** 3 gün  

#### Tapşırıqlar
- [ ] **4.3.1** Real-time FPS göstəricisi
- [ ] **4.3.2** Processing time qrafiki
- [ ] **4.3.3** Memory usage monitoring
- [ ] **4.3.4** GPU utilization (əgər mövcuddursa)
- [ ] **4.3.5** Performance alerts (FPS < threshold)

---

## 📅 Roadmap Xülasəsi

```
2025-Q1
├── Sprint 1 (Yan 1-14): Multi-camera, Tracking, Passive Enrollment
├── Sprint 2 (Yan 15-28): Test Coverage, Error Handling
├── Sprint 3 (Fev 1-14): i18n, Validation, Notifications
└── Sprint 4 (Fev 15-28): Database, Backup, Monitoring

2025-Q2 (Backlog)
├── Audit trail / Activity logs
├── Face enrollment UX (quality check)
├── License self-service portal
└── Mobile companion app (v2.0)
```

---

## 📊 Uğur Metrikaları

| Metrika | Cari | Hədəf | Sprint |
|---------|------|-------|--------|
| Test Coverage | ~10% | 60% | Sprint 2 |
| Kamera dəstəyi | 1 | 4+ | Sprint 1 |
| Ortalama bug həlli vaxtı | N/A | 2 gün | Sprint 2 |
| İstifadəçi şikayətləri (xəta görünmür) | Yüksək | 0 | Sprint 2 |

---

## 🔗 Əlaqədar Sənədlər

- `docs/TECH_SPEC.md` - Texniki spesifikasiya
- `docs/overview.md` - Sistem icmalı
- `docs/directory_structure.md` - Qovluq strukturu

---

## ✅ Təsdiq

| Rol | Ad | Tarix | İmza |
|-----|-----|-------|------|
| Product Manager | | | |
| Tech Lead | | | |
| QA Lead | | | |

---

*Bu sənəd avtomatik yaradılmışdır və dəyişikliklərə açıqdır.*
