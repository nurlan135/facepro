# FacePro - Project Brief

## Project Overview
**FacePro** is a smart security system that transforms existing CCTV/DVR cameras into an intelligent monitoring solution using local AI processing. The system runs entirely offline, making it ideal for security-conscious environments.

## Core Requirements

### Primary Goals
1. **Face Recognition** - Identify known individuals from a database of enrolled faces
2. **Person Re-ID** - Track individuals by clothing/body features when face is not visible
3. **Motion Detection** - CPU-efficient gatekeeper to trigger AI processing only when needed
4. **Object Detection** - Detect persons, cats, and dogs using YOLOv8
5. **Offline Operation** - All AI processing runs locally, no cloud dependency

### Secondary Goals
1. **Telegram Notifications** - Real-time alerts when connected to internet
2. **GSM Fallback** - SMS alerts via USB modem when offline
3. **Hardware License Lock** - Prevent unauthorized distribution
4. **FIFO Storage** - Automatic cleanup when disk space is full

## Target Audience
- Small businesses with existing CCTV infrastructure
- Homeowners wanting smart security without cloud subscriptions
- Security-conscious users who prefer local processing

## Success Criteria
- Detect and identify persons in real-time (< 500ms latency)
- Work with standard RTSP cameras and webcams
- Run on consumer hardware (i5 6th gen+, 8GB RAM)
- Function completely offline
- Provide clear visual feedback in the UI

## Project Constraints
- Must work on Windows 10/11
- PyQt6 for UI (cross-platform potential)
- SQLite for local database
- No external API dependencies for core functionality

## Timeline
- **Phase 1 (MVP)**: Core detection + UI dashboard ✅
- **Phase 2**: Telegram integration + Face enrollment UI ✅
- **Phase 3**: GSM SMS fallback + Settings ✅
- **Phase 4**: Re-ID integration + Analytics ✅
- **Phase 5**: UI Modularization + Multi-language ✅
- **Phase 6**: User Authentication + Gait Recognition ✅
- **Phase 7**: Handover Documentation + Security Audit ✅
- **Phase 8**: RTSP Testing + Production Hardening (Next)
