# FacePro - Smart Security System

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

> Lokal AI ilə işləyən ağıllı təhlükəsizlik sistemi. Köhnə kameralarınızı (RTSP/DVR) dəyişdirmədən ağıllı sisteme çevirin.

## 🎯 Xüsusiyyətlər

- **🔍 Üz Tanıma (Face Recognition)** - Tanınmış şəxsləri avtomatik aşkarlayır
- **👤 Person Re-ID** - Üzü görünməsə belə geyimindən tanıyır
- **🏃 Hərəkət Aşkarlama** - CPU qənaəti üçün ağıllı motion detection
- **📱 Telegram Bildirişləri** - Real-time xəbərdarlıqlar
- **📶 GSM Fallback** - İnternet olmadıqda SMS göndərir
- **💾 FIFO Saxlama** - Disk dolduqda köhnə faylları silir
- **🌙 Dark Theme** - Gözləri yormayan modern interfeys

## 📋 Sistem Tələbləri

| Komponent | Minimum | Tövsiyə |
|-----------|---------|---------|
| **CPU** | i5 (6th Gen) | i7 / Apple Silicon |
| **RAM** | 4GB | 8GB+ |
| **Python** | 3.10+ | 3.11+ |
| **OS** | Windows 10/11, macOS, Linux | Windows 11 |

## 🚀 Quraşdırma

### 1. Repository-ni klonlayın
```bash
git clone https://github.com/yourusername/facepro.git
cd facepro
```

### 2. Virtual environment yaradın
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Bağımlılıqları quraşdırın
```bash
pip install -r requirements.txt
```

### 4. Tətbiqi başladın
```bash
python main.py
```

## 📁 Layihə Strukturu

```
FacePro/
├── assets/              # Icons, logo, styles
├── config/
│   ├── settings.json    # Tətbiq konfiqurasiyası
│   └── cameras.json     # Kamera siyahısı
├── data/
│   ├── db/
│   │   └── faceguard.db # SQLite database
│   ├── faces/           # Tanınmış üz şəkilləri
│   └── logs/            # Hadisə snapshotları
├── models/              # AI modelləri
├── src/
│   ├── core/            # Əsas mühərrik
│   │   ├── camera_thread.py
│   │   ├── ai_thread.py
│   │   ├── reid_engine.py
│   │   └── cleaner.py
│   ├── hardware/        # Hardware inteqrasiyası
│   │   └── gsm_modem.py
│   ├── ui/              # PyQt6 interfeys
│   │   ├── main_window.py
│   │   ├── video_widget.py
│   │   ├── settings_dialog.py
│   │   └── styles.py
│   └── utils/           # Yardımçı funksiyalar
│       ├── logger.py
│       └── helpers.py
├── main.py              # Entry point
├── requirements.txt
└── README.md
```

## ⚙️ Konfiqurasiya

### Telegram Bot
1. [@BotFather](https://t.me/botfather)-dan bot yaradın
2. Settings → Notifications → Bot Token-ı daxil edin
3. Bot-a `/start` yazın və Chat ID-ni əldə edin

### Kamera əlavə etmək
1. Settings → Cameras → Add Camera
2. RTSP URL, Webcam və ya Video File seçin
3. Hikvision/Dahua brendləri avtomatik URL yaradır

### GSM Modem (Offline mode)
1. USB modemi qoşun (tövsiyə: Huawei E3372)
2. Settings → Notifications → GSM aktiv edin
3. COM port və telefon nömrəsini daxil edin

## 🎮 İstifadə

1. **Start** düyməsinə basın
2. Kameralar avtomatik qoşulacaq
3. AI real-time analiz edəcək
4. Aşkarlamalar Events panelində görünəcək
5. Telegram bildirişləri avtomatik göndəriləcək

## 📊 AI Pipeline

```
Frame → Motion Detection → Object Detection (YOLO) 
                              ↓
                     Person Detected?
                        ↓         ↓
                       Yes        No → Skip
                        ↓
              Face Recognition
                ↓           ↓
            Face Found   No Face
                ↓           ↓
          Return Name   Re-ID (Body)
                           ↓
                    Match in DB?
                     ↓       ↓
                   Yes       No
                    ↓        ↓
               Return    "Unknown"
                Name
```

## 🤝 Kömək

Problem və ya suallarınız üçün:
- Issue açın
- Pull request göndərin

## 📄 Lisenziya

Bu proqram xüsusi lisenziya ilə qorunur. Kommersiya istifadəsi üçün əlaqə saxlayın.

---

**FacePro** © 2025 NurMurDev. Bütün hüquqlar qorunur.
