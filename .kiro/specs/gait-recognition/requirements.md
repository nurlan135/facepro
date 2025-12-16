# Requirements Document

## Introduction

FacePro tətbiqi üçün yeriş tanıma (Gait Recognition) sistemi. Bu sistem üz görünmədikdə insanları yeriş xüsusiyyətlərinə görə tanımağa imkan verəcək. Mövcud Face Recognition və Re-ID sistemlərinə əlavə olaraq, üçüncü tanıma metodu kimi inteqrasiya olunacaq.

## Glossary

- **Gait_Recognition_System**: İnsanları yeriş xüsusiyyətlərinə görə tanıyan modul
- **Silhouette**: İnsanın qara-ağ siluet görüntüsü (background çıxarılmış)
- **Gait_Sequence**: Ardıcıl silhouette frame-lərdən ibarət video seqansı (30 frame)
- **Gait_Embedding**: Yeriş xüsusiyyətlərini təmsil edən 256 ölçülü vektor
- **Gait_Buffer**: Hər izlənən insan üçün frame-ləri toplayan buffer
- **Track_ID**: YOLO tərəfindən təyin edilən unikal insan izləmə identifikatoru
- **OpenGait**: Yeriş tanıma üçün istifadə olunan açıq mənbəli model kitabxanası

## Requirements

### Requirement 1

**User Story:** As a security operator, I want the system to recognize people by their walking pattern, so that I can identify individuals even when their face is not visible.

#### Acceptance Criteria

1. WHEN a person is detected and face recognition fails THEN the Gait_Recognition_System SHALL attempt to identify the person using gait analysis
2. WHEN a person walks through the camera view THEN the Gait_Recognition_System SHALL collect a minimum of 30 consecutive frames for analysis
3. WHEN gait analysis completes THEN the Gait_Recognition_System SHALL return a confidence score between 0 and 1
4. WHEN the confidence score exceeds 0.70 THEN the Gait_Recognition_System SHALL label the person with their name and "(Gait)" suffix

### Requirement 2

**User Story:** As a system administrator, I want gait patterns to be automatically learned when a person is identified by face, so that the system improves over time without manual enrollment.

#### Acceptance Criteria

1. WHEN face recognition successfully identifies a person THEN the Gait_Recognition_System SHALL extract and store the gait embedding for that person (Passive Enrollment)
2. WHEN storing a new gait embedding THEN the Gait_Recognition_System SHALL associate it with the user_id from the face recognition result
3. WHEN a user already has gait embeddings THEN the Gait_Recognition_System SHALL update the stored embeddings with new samples (maximum 10 per user)
4. WHEN the gait_embeddings table exceeds 10 entries per user THEN the Gait_Recognition_System SHALL remove the oldest embedding

### Requirement 3

**User Story:** As a developer, I want the gait recognition to integrate seamlessly with the existing AI pipeline, so that it works as a fallback when face and Re-ID fail.

#### Acceptance Criteria

1. WHEN the AI pipeline processes a frame THEN the Gait_Recognition_System SHALL follow this priority: Face Recognition → Re-ID → Gait Recognition
2. WHEN gait recognition is processing THEN the Gait_Recognition_System SHALL NOT block the main AI thread
3. WHEN multiple people are in frame THEN the Gait_Recognition_System SHALL maintain separate gait buffers for each tracked person
4. WHEN a tracked person leaves the frame THEN the Gait_Recognition_System SHALL clear their gait buffer after 5 seconds of absence

### Requirement 4

**User Story:** As a user, I want to see gait recognition results in the UI, so that I know when someone was identified by their walking pattern.

#### Acceptance Criteria

1. WHEN a person is identified by gait THEN the video overlay SHALL display a blue bounding box (distinct from green/face and yellow/Re-ID)
2. WHEN a person is identified by gait THEN the label SHALL show "Name (Gait: XX%)" format
3. WHEN gait analysis is in progress THEN the system SHALL show "Analyzing gait..." indicator on the bounding box
4. WHEN viewing event logs THEN the system SHALL indicate which identification method was used (Face/Re-ID/Gait)

### Requirement 5

**User Story:** As a system administrator, I want to configure gait recognition parameters, so that I can optimize performance for different environments.

#### Acceptance Criteria

1. WHEN accessing settings THEN the administrator SHALL be able to enable or disable gait recognition
2. WHEN configuring gait recognition THEN the administrator SHALL be able to set the minimum confidence threshold (default: 0.70)
3. WHEN configuring gait recognition THEN the administrator SHALL be able to set the sequence length (default: 30 frames)
4. WHEN the system starts THEN the Gait_Recognition_System SHALL load configuration from settings.json

### Requirement 6

**User Story:** As a developer, I want the silhouette extraction to be efficient, so that it doesn't significantly impact system performance.

#### Acceptance Criteria

1. WHEN extracting silhouettes THEN the Gait_Recognition_System SHALL use background subtraction optimized for the detected person's bounding box
2. WHEN processing silhouettes THEN the Gait_Recognition_System SHALL resize them to 64x64 pixels for model input
3. WHEN the CPU usage exceeds 80% THEN the Gait_Recognition_System SHALL skip gait analysis and rely on Re-ID only
4. WHEN gait analysis completes THEN the processing time SHALL NOT exceed 100ms per sequence

### Requirement 7

**User Story:** As a developer, I want gait embeddings stored in the database, so that they persist across application restarts.

#### Acceptance Criteria

1. WHEN storing gait embeddings THEN the Gait_Recognition_System SHALL use the gait_embeddings table in SQLite
2. WHEN loading the application THEN the Gait_Recognition_System SHALL load all gait embeddings into memory
3. WHEN comparing embeddings THEN the Gait_Recognition_System SHALL use cosine similarity
4. WHEN serializing embeddings THEN the Gait_Recognition_System SHALL use pickle for BLOB storage
