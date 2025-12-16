# Requirements Document

## Introduction

Bu xüsusiyyət FacePro tətbiqində kamera əlavə etmə prosesini yaxşılaşdırır. İstifadəçilər RTSP/IP kameralar və lokal (USB/webcam) kameralar üçün ayrı-ayrı, istifadəçi dostu konfiqurasiya dialoquları vasitəsilə kamera əlavə edə biləcəklər. Sistem lokal kameraları avtomatik aşkarlayacaq və önizləmə ilə göstərəcək.

## Glossary

- **RTSP**: Real Time Streaming Protocol - IP kameralardan video axını üçün protokol
- **IP Kamera**: Şəbəkə üzərindən bağlanan təhlükəsizlik kamerası (Hikvision, Dahua, TP-Link və s.)
- **Lokal Kamera**: Kompüterə USB və ya daxili olaraq bağlı kamera (webcam, laptop kamerası)
- **Device ID**: OpenCV-nin kameranı tanımaq üçün istifadə etdiyi indeks nömrəsi
- **Önizləmə**: Kameradan alınan canlı görüntünün kiçik versiyası
- **Endpoint**: RTSP URL-in son hissəsi (məsələn, /stream1, /Streaming/Channels/101)

## Requirements

### Requirement 1: Kamera Növü Seçimi

**User Story:** As a user, I want to select camera type before configuration, so that I can see only relevant options for my camera.

#### Acceptance Criteria

1. WHEN a user clicks "Add Camera" button THEN the System SHALL display a camera type selection dialog with two options: RTSP/IP Camera and Local Camera
2. WHEN a user selects RTSP/IP Camera option THEN the System SHALL navigate to RTSP configuration dialog
3. WHEN a user selects Local Camera option THEN the System SHALL navigate to local camera selection dialog
4. WHEN a user clicks cancel button THEN the System SHALL close the dialog without adding any camera

### Requirement 2: RTSP Kamera Konfiqurasiyası

**User Story:** As a user, I want to configure RTSP camera with separate fields, so that I can easily enter connection details without knowing the full URL format.

#### Acceptance Criteria

1. WHEN RTSP configuration dialog opens THEN the System SHALL display separate input fields for: IP Address, Port, Username, Password, and Endpoint/Path
2. WHEN a user enters connection details THEN the System SHALL automatically generate and display the full RTSP URL in real-time
3. WHEN a user enters password THEN the System SHALL mask the password in the generated URL preview with asterisks
4. WHEN a user clicks "Test Connection" button THEN the System SHALL attempt to connect to the camera and display success or failure message
5. WHEN connection test is in progress THEN the System SHALL display a loading indicator and disable the test button
6. WHEN a user clicks "Back" button THEN the System SHALL return to camera type selection dialog
7. WHEN a user clicks "Save" button with valid configuration THEN the System SHALL save the camera and close the dialog

### Requirement 3: Lokal Kamera Aşkarlama və Seçimi

**User Story:** As a user, I want to see all available local cameras with previews, so that I can easily identify and select the correct camera.

#### Acceptance Criteria

1. WHEN local camera dialog opens THEN the System SHALL automatically scan for all connected cameras
2. WHILE scanning for cameras THEN the System SHALL display a loading indicator with "Scanning cameras..." message
3. WHEN cameras are found THEN the System SHALL display each camera as a card with: camera name, resolution, device ID, and live preview thumbnail
4. WHEN no cameras are found THEN the System SHALL display "No cameras found" message with troubleshooting suggestions
5. WHEN a user clicks "Select This Camera" button on a camera card THEN the System SHALL save the camera configuration and close the dialog
6. WHEN a user clicks "Back" button THEN the System SHALL return to camera type selection dialog
7. WHEN dialog closes THEN the System SHALL stop all camera preview streams to free resources

### Requirement 4: Kamera Önizləmə

**User Story:** As a user, I want to see live preview from cameras, so that I can verify the camera is working correctly before adding it.

#### Acceptance Criteria

1. WHEN local camera card is displayed THEN the System SHALL show a live preview thumbnail updated every 500ms
2. WHEN camera preview fails to load THEN the System SHALL display a placeholder image with error icon
3. WHEN RTSP connection test succeeds THEN the System SHALL optionally show a single frame preview from the camera
4. WHEN multiple cameras are being previewed THEN the System SHALL limit concurrent preview streams to prevent performance issues

### Requirement 5: Xəta İdarəetməsi

**User Story:** As a user, I want to see clear error messages, so that I can understand and fix connection problems.

#### Acceptance Criteria

1. WHEN RTSP connection fails THEN the System SHALL display specific error message indicating the failure reason (timeout, authentication, network)
2. WHEN local camera access fails THEN the System SHALL display error message with possible causes (camera in use, permission denied)
3. WHEN required fields are empty THEN the System SHALL highlight the fields and prevent form submission
4. WHEN IP address format is invalid THEN the System SHALL display validation error message
