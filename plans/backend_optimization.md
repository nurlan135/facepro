# Backend Optimizasiya və Refaktorinq Planı
**Tarix:** 22 Dekabr 2025
**Status:** İcra Olundu (Faza 1, 2, 3 + POC)
**Prioritet:** Yüksək

Bu sənəd `FacePro` layihəsinin backend hissəsində mövcud olan arxitektur problemləri, performans darboğazlarını (bottlenecks) və onların həlli yollarını əhatə edir.

## 1. Cari Problemlərin Analizi

### 1.1. Performans Darboğazı (Blocking I/O)
*   **Problem:** `AIWorker` (AI Thread) hər tanımdan sonra (Re-ID, Face Recognition) nəticələri birbaşa `EmbeddingRepository` vasitəsilə SQLite bazasına yazır.
*   **Təsir:** SQLite disk əməliyyatları (I/O) zamanı "Block" olur. Bu zaman AI pipeline dayanıb gözləyir, nəticədə FPS (Kadr/saniyə) kəskin düşür və video axınında gecikmələr olur.
*   **Risk:** Yüksək
*   **Həll:** Asinxron I/O (Producer-Consumer Pattern).

### 1.2. Mərkəzləşmiş Mürəkkəblik ("God Object")
*   **Problem:** `ai_thread.py` faylındakı `AIWorker` sinfi həddindən artıq çox məsuliyyət daşıyır: Kamera oxuma, Motion Detection, Obyekt Tanıma, Üz Tanıma, Re-ID, Gait, Keşləmə və DB Yazma.
*   **Təsir:** Kodu test etmək, sazlamaq (debug) və yeni funksiya əlavə etmək (maintainability) çox çətindir.
*   **Risk:** Orta
*   **Həll:** Məntiqin `Service` qatlarına bölünməsi.

### 1.3. Verilənlər Bazası Şişməsi (Database Bloat)
*   **Problem:** Böyük həcmli vektorlar (Re-ID embeddings) və binar datalar birbaşa `reid_embeddings` cədvəlində `BLOB` kimi saxlanılır.
*   **Təsir:** `.db` faylı çox sürətlə böyüyür. Böyük fayl sorğuların sürətini azaldır və backup/restore prosesini çətinləşdirir.
*   **Risk:** Orta
*   **Həll:** Vektorların optimallaşdırılmış saxlanması və ya `VACUUM` strategiyası.

### 1.4. Texniki Borclar (Technical Debt)
*   **Dlib Asılılığı:** `dlib` kitabxanası Windows mühitində çətin quraşdırılır (C++ compiler tələbi) və ağırdır. Gələcəkdə `ONNX Runtime` (InsightFace) keçidi zəruridir.
*   **Miqrasiya Yoxdur:** DB sxemində dəyişiklik edildikdə köhnə versiyaların yenilənməsi üçün avtomatik alət (`Alembic`) yoxdur.

---

## 2. Həll Strategiyası (Faza-Faza)

### Faza 1: "Fire-and-Forget" (Asinxron Yazma) - **Kritik**
Ən vacib addım AI Thread-i DB yükündən azad etməkdir.

1.  **StorageWorker Yaratmaq:** `QThread` əsaslı yeni bir `StorageWorker` yaradılmalı.
2.  **Queue Sistemi:** `AIWorker` və `StorageWorker` arasında thread-safe `Queue` (Növbə) qurulmalı.
3.  **Məntiq:** `AIWorker` tanıma etdikdən sonra datanı (embedding, şəkil, metadata) sadəcə Queue-ya atır (push) və dərhal növbəti kadra keçir. `StorageWorker` arxa planda bu Queue-nu oxuyub bazaya yazır.

### Faza 2: Verilənlər Bazası Arxitekturası (Repository Refactoring)
DB qatını daha təmiz və təhlükəsiz etmək.

1.  **Transaction Management:** `DatabaseManager`-də `contextmanager` istifadə edərək transaction-ları (commit/rollback) avtomatlaşdırmaq.
2.  **Batch Inserts:** Tək-tək `INSERT` əvəzinə, Queue-dan gələn dataları qruplaşdırıb toplu (Batch) şəkildə yazmaq (SQLite üçün çox daha sürətlidir).
3.  **Connection Pooling:** Eyni anda UI oxuması və Backend yazması zamanı "Database locked" xətasının qarşısını almaq üçün WAL (Write-Ahead Logging) rejimini aktivləşdirmək: `PRAGMA journal_mode=WAL;`.

### Faza 3: Moduallaşdırma (Service Layer)
`AIWorker` sinfini sadələşdirmək.

1.  **Services:** Məntiqi aşağıdakı servislərə bölmək:
    *   `DetectionService`: Yalnız YOLO işləri.
    *   `RecognitionService`: Üz və Re-ID məntiqi.
    *   `MatchingService`: Vektorların müqayisəsi və Matrix əməliyyatları.
2.  **AIWorker Rolu:** `AIWorker` sadəcə orkestrator (koordinator) rolunu oynamalıdır.

---

## 3. İcra Planı (Action Items)

- [x] **Task 1:** `src/core/storage_worker.py` faylını yaratmaq (Queue və DB Insert məntiqi ilə).
- [x] **Task 2:** `src/core/ai_thread.py` faylında birbaşa DB çağırışlarını silib, `storage_queue.put()` ilə əvəz etmək.
- [x] **Task 3:** `src/core/database/db_manager.py` faylında `WAL` rejimini aktivləşdirmək.
- [x] **Task 3.1:** `Batch Insert` dəstəyini Repositoriyalara əlavə etmək.
- [x] **Task 4:** `EmbeddingRepository` sinfini "Thread-Safe" etmək (Connection idarəetməsi).
- [x] **Task 4.5:** `RecognitionService` (Tanıma və Re-ID məntiqinin ayrılması).
- [x] **Task 4.6:** `DetectionService` (YOLO və Motion Detection məntiqinin ayrılması).
- [x] **Task 4.7:** `AIWorker`-i Servislərə inteqrasiya etmək.
- [x] **Task 4.8:** `MatchingService` (Vektor müqayisə və yaddaş idarəsi).
- [x] **Task 5 (POC Hazırdır):** `dlib` -> `insightface` miqrasiyası proqress (benchmark skripti).

bu sənəd layihənin backend inkişafı üçün yol xəritəsidir.
