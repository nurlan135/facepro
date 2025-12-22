---
trigger: always_on
---

# Project Rules & Guidelines: FaceGuardPro (FacePro)

## 1. Layihə Fəlsəfəsi və Məhdudiyyətlər
* **Privacy-First (Məxfilik):** Bütün məlumatlar (şəkillər, videolar, verilənlər bazası) **LOKALDA** qalmalıdır. Heç vaxt bulud (Cloud) həlləri təklif etmə (Telegram Bot və GSM xaric).
* **Offline-First:** Sistem internet olmadan da tam işlək olmalıdır. İnternet asılılığı olan kitabxanalar istifadə etmə.
* **Resource-Aware:** Hədəf cihazlar 4GB RAM-a malik ola bilər. Yaddaş sızmasına (Memory Leak) yol vermə.

## 2. Texniki Stack (Dəyişdirilməz)
* **Dil:** Python 3.10+
* **GUI Framework:** PyQt6 (Qətiyyən Tkinter və ya Kivy istifadə etmə).
* **Computer Vision:**
    *   Object Detection: YOLOv8n (`ultralytics`) - Person, Cat, Dog.
    *   Face Recognition: `dlib` + `face_recognition`.
    *   Re-ID (Body): `EfficientNet-B0` (PyTorch).
    *   Gait Recognition: `ResNet18` (Silhouette-based, PyTorch).
* **Database:** SQLite (`data/db/facepro.db`).
* **Build Tool:** PyInstaller (One-file və ya One-dir).
* **Security:** `bcrypt` (password hashing), `numpy` (serialization).

## 3. Kodlama Standartları

### 3.1. Threading & Concurrency (Çox Vacib!)
* **Qızıl Qayda:** GUI (Main Thread) heç vaxt donmamalıdır.
* **RTSP/Kamera:** `cv2.VideoCapture` funksiyası MÜTLƏQ ayrı bir `QThread` (`CameraWorker`) daxilində işləməlidir.
* **AI Emalı:** YOLO, Face, Re-ID və Gait hesablamaları MÜTLƏQ `AIWorker` (QThread) daxilində aparılmalıdır.
* **Communication:** Thread-lər arasında məlumat ötürmək üçün yalnız PyQt `pyqtSignal` istifadə et (Shared global variables yox).

### 3.2. Kod Stili
* **PEP 8:** Bütün kodlar PEP 8 standartına uyğun olmalıdır.
* **Type Hinting:** Funksiya arqumentləri və dönüş dəyərləri üçün tip göstəriciləri istifadə et (məs: `def process_frame(frame: np.ndarray) -> dict:`).
* **Logging:** `print()` funksiyasını QƏTİYYƏN istifadə etmə. Layihənin mərkəzi `src.utils.logger` modulunu istifadə et (`logger.info`, `logger.error`).

### 3.3. Xəta İdarəetməsi (Error Handling)
* **Kamera Qopması:** `cv2.read()` boş (None) qayıdarsa, proqram çökə bilməz. "Reconnecting..." statusuna keçib 5 saniyədən bir yenidən qoşulmağa cəhd etməlidir.
* **Model Yüklənməsi:** Əgər GPU (CUDA) yoxdursa, avtomatik və səssizcə CPU rejiminə keç.

### 3.4. Təhlükəsizlik (Security)
* **Serialization:** `pickle` modulu təhlükəsizlik riski yaratdığı üçün (RCE) **QADAĞANDIR**. Yalnız `numpy.tobytes()` və `numpy.frombuffer()` istifadə et.
* **Secrets:** API açarları (Telegram Token, License Salt) kodun içində və ya Git-ə düşən fayllarda saxlanmamalıdır. Environment Variable (`os.environ`) istifadə et.
* **Passwords:** Şifrələri heç vaxt plaintext saxlama. Yalnız `bcrypt` hash-lərini saxla.

## 4. Spesifik Biznes Məntiqi (Business Logic)

### 4.1. Lisenziya (Hardware Lock)
* Sistem `main.py` işə düşən kimi lisenziya faylını (`.license`) yoxlamalıdır.
* Lisenziya yoxdursa və ya `MachineID` (CPU+Mobo) uyğun gəlmirsə, yalnız "Aktivasiya Pəncərəsi" açılmalıdır.
* Bypass (yan keçmə) imkanlarını minimuma endir.

### 4.2. "Soyuq Başlanğıc" (Passive Enrollment)
* İstifadəçi yalnız ÜZ şəkli yükləyir.
* Sistem:
    1.  Üz tanınan kimi -> Həmin kadrın BƏDƏN vektorunu (Re-ID) çıxar -> `reid_embeddings` cədvəlinə yaz.
    2.  Həmin şəxsin YERİŞ (Gait) ardıcıllığını topla -> `gait_embeddings` cədvəlinə yaz.
* Bu məntiq `src/core/reid_engine.py` və `src/core/gait_engine.py` daxilində olmalıdır.

### 4.3. Yaddaş Təmizliyi (FIFO)
* `src/core/cleaner.py` daxilində arxa planda işləyən bir proses olmalıdır.
* Qovluq ölçüsü > LIMIT (məs: 10GB) olarsa, ən köhnə faylları silməlidir.

## 5. Qadağalar (Anti-Patterns)
* ❌ `time.sleep()` funksiyasını GUI thread-də istifadə etmə (bunun əvəzinə `QTimer`).
* ❌ API açarlarını hard-code etmə.
* ❌ `pickle` istifadə etmə.
* ❌ Mütləq yollar (Absolute Paths) istifadə etmə. `os.path.join` və ya `pathlib` istifadə et.
* ❌ `tkinter` və ya `kivy` modullarını import etmə.

## 6. Agent Workflow
1.  Kodu yazmazdan əvvəl həmişə `docs/TECH_SPEC.md` və `docs/overview.md` fayllarını oxu.
2.  Yeni fayl yaradanda `docs/directory_structure.md` strukturuna sadiq qal.
3.  Hər hansı bir funksiyanı dəyişərkən onun mövcud testləri (əgər varsa) pozmadığından əmin ol.
4.  Təhlükəsizlik qaydalarına (NO pickle, NO hardcoded secrets) ciddi riayət et.