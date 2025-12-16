# FacePro - Product Context

## Why This Project Exists

### The Problem
1. **Existing CCTV systems are dumb** - They only record video, no real-time intelligence
2. **Cloud-based solutions are expensive** - Monthly subscriptions add up
3. **Privacy concerns** - Users don't want video going to external servers
4. **Connectivity dependency** - Cloud solutions fail when internet is down

### The Solution
FacePro adds AI intelligence to existing camera infrastructure:
- **No new cameras needed** - Works with any RTSP-compatible camera
- **One-time purchase** - No subscriptions
- **100% local processing** - No data leaves the property
- **Offline capable** - GSM fallback for alerts

## How It Should Work

### User Journey
1. **Installation**: User installs FacePro, enters license key
2. **Camera Setup**: Add existing cameras via Settings → Cameras
3. **Face Enrollment**: Upload photos of known persons (family, employees)
4. **Monitoring**: System runs 24/7, detecting and identifying people
5. **Alerts**: User receives Telegram/SMS when unknown person detected

### Detection Flow
```
Camera Frame → Motion Check → Object Detection → Face Recognition → Re-ID → Gait → Alert
                   ↓                 ↓                   ↓            ↓        ↓
               (skip if           (filter for        (known?      (match   (match by
                no motion)        person/cat/dog)     identify)   clothing) walking)
```

## User Experience Goals

### Visual Design
- **Dark theme** - Easy on the eyes for 24/7 monitoring
- **Grid layout** - View multiple cameras at once
- **Clear indicators** - Green for known, Red for unknown
- **Event history** - Scroll through recent detections

### Interaction Patterns
- **Start/Stop** - Single button to control monitoring
- **Settings accessible** - Quick access to configuration
- **Minimal clicks** - Streamlined workflows

### Performance Expectations
- **Real-time video** - No noticeable lag (30 FPS target)
- **Quick detection** - < 500ms from detection to UI update
- **Responsive UI** - No freezing during AI processing

## Key Differentiators
1. **Re-ID capability** - Track people even when face isn't visible
2. **Gait Recognition** - Identify people by walking pattern (NEW)
3. **GSM fallback** - Alerts work even without internet
4. **Hardware lock** - Prevents piracy, protects commercial value
5. **Local-first** - Privacy by design
6. **Multi-language** - English, Azerbaijani, Russian with live switching
7. **Modular UI** - Modern dashboard design with sidebar, tabs, filters
