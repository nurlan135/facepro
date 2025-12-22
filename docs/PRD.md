# Product Requirements Document (PRD)

## 1. Metada və Versiya İdarəsi (Metadata & Version History)

| Məlumat | Təfərrüat |
| :--- | :--- |
| **Layihə Adı** | FacePro |
| **Versiya** | **1.0 (MVP - Final Technical Release)** |
| **Status** | **Approved (Təsdiqləndi)** |
| **Tarix** | 15 Dekabr 2025 |
| **Platforma** | Desktop (Windows 10/11, macOS, Linux) |
| **Biznes Modeli** | Lifetime License (Birdəfəlik Lisenziya) |

### Versiya Tarixçəsi
| Versiya | Tarix | Dəyişiklik Təsviri | Məsul |
| :--- | :--- | :--- | :--- |
| 1.0 | 01.12.2025 | Konseptual qaralama | NurMurDev |
| 1.1 | 15.12.2025 | Re-ID "Soyuq Başlanğıc", RAM Optimizasiyası və GSM/Offline modulu əlavə edildi | NurMurDev |

---

## 2. Problemin Təsviri və Vizyon (Problem & Vision)

### 2.1. Problem
İstifadəçilər köhnə təhlükəsizlik sistemlərini (DVR/NVR) yeniləmək istədikdə üç əsas maneə ilə üzləşirlər:
1.  **Məxfilik və Xərc:** Müasir bulud sistemləri (Ring, Nest) aylıq abunə haqqı tələb edir və video görüntüləri xarici serverlərə göndərir.
2.  **İnternet Asılılığı:** Bağ evləri və ya tikinti sahələri kimi interneti olmayan ərazilərdə "ağıllı" bildiriş almaq mümkün deyil.
3.  **Yarımçıq Tanıma:** Mövcud sistemlər (Motion Detection) sadəcə "hərəkət var" deyir, oğrunu və ya ailə üzvünü ayırd edə bilmir.

### 2.2. Vizyon
**FaceGuardPro**, mövcud köhnə kameraları (RTSP) və ya veb-kameraları dəyişdirmədən onları **lokal işləyən (Edge AI)**, internet olmadıqda belə SMS göndərə bilən və insanı üzü görünməsə belə geyimindən tanıyan (Re-ID) super-ağıllı təhlükəsizlik sisteminə çevirir.

---

## 3. Hədəflər və Uğur Kriteriyaları (Goals & KPIs)

### 3.1. Biznes Hədəfləri
* **MVP Buraxılışı:** 4 həftə ərzində tam işlək, quraşdırıla bilən `.exe` faylı.
* **Köhnə Sistemlərə Dəstək:** Bazardakı DVR-ların (Hikvision, Dahua) 90%-i ilə uyğunluq.

### 3.2. Uğur Metrikaları (KPIs)
| Metrika | Hədəf | Qeyd |
| :--- | :--- | :--- |
| **Re-ID Effektivliyi** | > 80% | Üzü görünməyən, lakin əvvəl qeydə alınmış şəxsin tanınma dəqiqliyi. |
| **False Positive Rate** | < 5 / gün | Gündəlik yalançı bildiriş (milçək, kölgə) sayı. |
| **Sistem Yükü** | < 60% CPU | 8GB RAM-lı cihazda arxa planda işləyərkən. |
| **Offline Reaksiya** | < 15 san | İnternet kəsildikdə GSM modulu ilə SMS göndərmə sürəti. |

---

## 4. Hədəf Auditoriya (User Personas)

1.  **Kənan (Kiçik Biznes):** Köhnə kameraları var. Dükanına girənin "Daimi müştəri" yoxsa "Yad" olduğunu Telegram-da görmək istəyir.
2.  **Aytən (Məxfilik):** Evin görüntülərinin internetə çıxmasını istəmir. Uşaq beşiyindən çıxanda xəbər tutmaq istəyir (Zone Intrusion).
3.  **Tural (Tikinti/DIY):** İnterneti olmayan tikinti sahəsində materialları qorumaq üçün GSM dəstəkli, elektriksiz (batareya/UPS ilə) işləyə bilən sistem axtarır.

---

## 5. Xüsusiyyətlər və Tələblər (Features & Requirements)

### 5.1. Video Girişi və İdarəetmə
* **Auto-Discovery:** Şəbəkədəki ONVIF kameraları avtomatik tapmalıdır.
* **RTSP Builder:** İstifadəçi IP, Login və Şifrə yazdıqda URL-i avtomatik yaratmalıdır (Hikvision/Dahua şablonları ilə).
* **Connection Healing:** Kamera bağlantısı qırılarsa (qara ekran), sistem hər 5 saniyədən bir təkrar qoşulmağa cəhd etməlidir.

### 5.2. AI Mühərriki (Core Intelligence)
* **Pipeline Ardıcıllığı:**
    1.  **Motion Detection:** Piksel dəyişikliyi yoxdursa, AI işə düşmür (CPU qənaəti).
    2.  **Object Detection (YOLOv8n-int8):** Yalnız "Person", "Cat", "Dog" sinifləri.
    3.  **Face Recognition:** Üz aydındırsa -> Tanı və Bədən Vektorunu yenilə.
    4.  **Person Re-ID (EfficientNet-B0):** Üz yoxdursa -> Bədən/Geyim vektorunu bazadakı son profillərlə müqayisə et.
* **Passive Enrollment (Soyuq Başlanğıc):** İstifadəçi sadəcə üz şəkli yükləyir. Sistem ilk dəfə üzü görən kimi, həmin kadrda bədən xüsusiyyətlərini avtomatik öyrənir və profilə əlavə edir.

### 5.3. Saxlama və Arxiv (Storage)
* **Lokal DB:** Bütün hadisələr (Metadata) `SQLite` bazasında saxlanılır.
* **FIFO Policy:** Disk dolmağa başlayanda (Tənzimlənən limit, məs: 10GB), ən köhnə şəkil/videolar avtomatik silinir.

### 5.4. Bildiriş və Offline Rejim
* **Telegram Bot:** Şəkil + [Tanıdığı Ad / Yad] + Tarix + Güvən Faizi.
* **GSM Fallback:**
    * İnternet bağlantısını yoxla (`ping 8.8.8.8`).
    * Əgər İnternet YOXDURSA -> USB Portdakı Modemi (COM port) yoxla.
    * AT Komandası ilə SMS göndər: *"DİQQƏT: Obyektdə hərəkət var! (İnternet kəsilib)"*.

### 5.5. Təhlükəsizlik Jurnalı (Audit Trail)
* **Tam Nəzarət:** İnzibati hərəkətlərin (Giriş/Çıxış, Ayarlar, İstifadəçi silinməsi) qeydiyyatı.
* **Şəffaflıq:** Hansı istifadəçinin nə vaxt hansı dəyişikliyi etdiyini izləmək imkanı.

---

## 6. Texniki Spesifikasiyalar (Technical Specs)

### 6.1. Stack
* **Backend:** Python 3.10+
* **UI Framework:** PyQt6 (Modern, Dark Theme)
* **Database:** SQLite (lokal fayl: `faceguard.db`)
* **AI Models:**
    * Object: `yolov8n.pt` (Quantized/Exported to ONNX for speed).
    * Face: `InsightFace` (ArcFace) - daha dəqiq və sürətli (512d vektor). Legacy dəstək: `dlib`.
    * Re-ID: `osnet_x1_0` və ya `efficientnet_b0` (Feature Extractor).
* **Hardware Integration:** `pyserial` (GSM Modem üçün).

### 6.2. Donanım Tələbləri
* **Minimum:** CPU i5 (6-cı nəsil), 4GB RAM (Low Performance Mode - 5 FPS).
* **Tövsiyə:** CPU i7 / Apple Silicon, 8GB+ RAM, GPU (Opsional).

---

## 7. İnterfeys (UI/UX) Strukturu

* **Dashboard:**
    * Canlı Video (Grid görünüşü - 1 və ya 4 kamera).
    * Sağ panel: Son Hadisələr (Şəkilli siyahı).
    * Alt bar: CPU, RAM, Disk, İnternet/GSM statusu.
* **Settings:**
    * Kamera əlavə etmə.
    * Üz İdarəetməsi (Şəkil yükləmə).
    * Bildiriş Ayarları (Telegram Token, GSM COM Port).
    * Zonalar (ROI) - Videonun üzərində qırmızı xətt çəkmə.

---

## 8. Asılılıqlar və Risklər (Dependencies & Risks)

| Risk | Təsir | Həll Planı (Mitigation) |
| :--- | :--- | :--- |
| **Yüksək Resurs İstifadəsi** | Proqram donur, PC qızır. | Frame Skipping (hər 5-ci kadrı analiz et) + Quantized Modellər. |
| **Köhnə DVR (H.265)** | Görüntü açılmır (boz ekran). | İstifadəçiyə "DVR-ı H.264-ə keçirin" xəbərdarlığı göstərmək. |
| **GSM Driver Problemi** | Modem tanınmır. | Standart "Huawei E3372" (HiLink olmayan) modemi tövsiyə etmək. |
| **Quraşdırma Çətinliyi** | İstifadəçi Python bilmir. | `PyInstaller` + `Inno Setup` ilə tək bir "Setup.exe" faylı hazırlamaq. |

---

## 9. Vaxt Cədvəli (Timeline)

* **Həftə 1:** Core Engine (Kamera oxuma + AI Modellerin inteqrasiyası).
* **Həftə 2:** Logic (Re-ID alqoritmi, GSM Fallback, FIFO saxlama).
* **Həftə 3:** UI Development (PyQt6 Dashboard, Ayarlar).
* **Həftə 4:** Paketləmə (.exe), Testlər və İlk Buraxılış.

---

## 10. GTM və Əlavələr (Appendix)

* **Satış Strategiyası:** Yerli inteqratorlarla tərəfdaşlıq (Köhnə müştəriləri upgrade etmək).
* **Lisenziyalaşdırma:** Offline "Serial Key" sistemi (Sadə alqoritmik yoxlama).
* **Gələcək Plan (SaaS):** Gələcəkdə uzaqdan izləmə üçün "Cloud Connector" əlavə ediləcək.