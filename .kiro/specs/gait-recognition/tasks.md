# Implementation Plan

- [x] 1. Database schema and GaitEngine core





  - [x] 1.1 Add gait_embeddings table to database schema


    - Add migration to `src/utils/helpers.py` (_ensure_db_initialized)
    - Include: id, user_id, embedding (BLOB), confidence, captured_at
    - Add index on user_id for faster lookups
    - _Requirements: 7.1_
  

  - [x] 1.2 Create GaitEngine class (`src/core/gait_engine.py`)

    - Singleton pattern with `get_gait_engine()` function
    - Lazy loading for model
    - Constants: SEQUENCE_LENGTH=30, SILHOUETTE_SIZE=(64,64), EMBEDDING_DIM=256
    - _Requirements: 1.2, 6.2_
  
  - [x] 1.3 Write property test for silhouette size consistency


    - **Property 3: Silhouette Size Consistency**
    - **Validates: Requirements 6.2**

- [x] 2. Silhouette extraction





  - [x] 2.1 Implement extract_silhouette method


    - Input: frame (BGR), bbox (x1,y1,x2,y2)
    - Background subtraction using MOG2 or simple thresholding
    - Crop to bbox, convert to grayscale, threshold to binary
    - Resize to 64x64
    - _Requirements: 6.1, 6.2_
  
  - [x] 2.2 Write property test for silhouette extraction


    - **Property 3: Silhouette Size Consistency**
    - **Validates: Requirements 6.2**

- [x] 3. Gait embedding extraction





  - [x] 3.1 Implement GaitSet model loading


    - Use pretrained GaitSet or simple CNN feature extractor
    - Fallback to torchvision ResNet18 if GaitSet unavailable
    - Input: 30 silhouettes (30x64x64)
    - Output: 256D embedding vector
    - _Requirements: 1.2_
  
  - [x] 3.2 Implement extract_embedding method


    - Stack 30 silhouettes into tensor
    - Pass through model
    - L2 normalize output
    - _Requirements: 1.2, 1.3_
  
  - [x] 3.3 Write property test for confidence score range


    - **Property 1: Confidence Score Range**
    - **Validates: Requirements 1.3**

- [x] 4. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. GaitBufferManager implementation




  - [x] 5.1 Create GaitBuffer dataclass


    - track_id, silhouettes list, last_update timestamp
    - _Requirements: 3.3_
  
  - [x] 5.2 Implement GaitBufferManager class


    - Dictionary of track_id → GaitBuffer
    - add_frame(track_id, silhouette) → bool (True when 30 reached)
    - get_sequence(track_id) → List[np.ndarray]
    - cleanup_stale() → remove buffers inactive for 5 seconds
    - _Requirements: 1.2, 3.3, 3.4_
  
  - [x] 5.3 Write property test for buffer sequence length


    - **Property 2: Buffer Sequence Length**
    - **Validates: Requirements 1.2**
  
  - [x] 5.4 Write property test for buffer isolation


    - **Property 7: Buffer Isolation**
    - **Validates: Requirements 3.3**

- [x] 6. Embedding comparison and matching





  - [x] 6.1 Implement cosine_similarity static method


    - Input: two numpy arrays
    - Output: float [0, 1]
    - _Requirements: 7.3_
  
  - [x] 6.2 Implement compare_embeddings method


    - Query embedding vs stored embeddings list
    - Return GaitMatch if confidence >= threshold
    - _Requirements: 1.3, 1.4_
  
  - [x] 6.3 Write property test for cosine similarity symmetry


    - **Property 5: Cosine Similarity Symmetry**
    - **Validates: Requirements 7.3**
  
  - [x] 6.4 Write property test for threshold configuration


    - **Property 9: Threshold Configuration**
    - **Validates: Requirements 5.2**

- [x] 7. Database operations








  - [x] 7.1 Implement save_embedding method


    - Serialize with pickle
    - Insert into gait_embeddings table
    - Enforce max 10 per user (delete oldest if exceeded)
    - _Requirements: 2.2, 2.3, 2.4, 7.1, 7.4_
  

  - [x] 7.2 Implement load_embeddings method





    - Load all embeddings from database on startup
    - Deserialize with pickle
    - Return list of (id, user_id, user_name, embedding)
    - _Requirements: 7.2_
  
  - [x] 7.3 Write property test for serialization round-trip






    - **Property 4: Embedding Serialization Round-Trip**
    - **Validates: Requirements 7.4**
  
  - [x] 7.4 Write property test for max embeddings per user





    - **Property 6: Maximum Embeddings Per User**
    - **Validates: Requirements 2.3, 2.4**

- [x] 8. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. AIWorker integration



  - [x] 9.1 Add GaitEngine and GaitBufferManager to AIWorker


    - Import and initialize in __init__
    - Load embeddings in run() method
    - _Requirements: 3.1_
  


  - [x] 9.2 Implement _try_gait_recognition method
    - Extract silhouette from frame/bbox
    - Add to buffer for track_id
    - If buffer full (30), extract embedding and compare
    - Return GaitMatch or None
    - _Requirements: 1.1, 3.1_
  
  - [x] 9.3 Implement passive gait enrollment
    - When face recognition succeeds, extract silhouette
    - Add to buffer, when full save embedding with user_id
    - _Requirements: 2.1, 2.2_
  
  - [x] 9.4 Update _process_frame for gait fallback

    - After Re-ID fails, try gait recognition
    - Set detection.label = "Name (Gait: XX%)"
    - _Requirements: 1.1, 1.4, 3.1_
  
  - [x] 9.5 Write property test for passive enrollment association



    - **Property 10: Passive Enrollment Association**
    - **Validates: Requirements 2.1, 2.2**

- [x] 10. UI updates





  - [x] 10.1 Update draw_detections for gait color


    - Blue bounding box for gait-identified persons
    - Label format: "Name (Gait: XX%)"
    - _Requirements: 4.1, 4.2_

  
  - [x] 10.2 Write property test for label format

    - **Property 8: Label Format Correctness**
    - **Validates: Requirements 1.4, 4.2**
  
  - [x] 10.3 Update Detection dataclass


    - Add identification_method field: 'face', 'reid', 'gait'
    - _Requirements: 4.4_

- [x] 11. Settings integration





  - [x] 11.1 Add gait settings to settings.json schema


    - gait_enabled: bool (default: true)
    - gait_threshold: float (default: 0.70)
    - gait_sequence_length: int (default: 30)
    - _Requirements: 5.1, 5.2, 5.3_
  

  - [x] 11.2 Update SettingsDialog for gait configuration

    - Enable/disable checkbox
    - Threshold slider (0.5 - 0.95)
    - Sequence length spinner (20-60)
    - _Requirements: 5.1, 5.2, 5.3_
  

  - [x] 11.3 Load gait settings on startup

    - Read from settings.json in GaitEngine init
    - _Requirements: 5.4_

- [x] 12. Event logging





  - [x] 12.1 Update events table for identification method


    - Add identification_method column if not exists
    - Values: 'face', 'reid', 'gait', 'unknown'
    - _Requirements: 4.4_
  
  - [x] 12.2 Update event creation to include method


    - Set identification_method when saving event
    - _Requirements: 4.4_

- [x] 13. i18n translations






  - [x] 13.1 Add gait-related translation keys

    - gait_recognition, gait_enabled, gait_threshold, etc.
    - Languages: en, az, ru
    - _Requirements: 4.2, 4.3_

- [x] 14. Final Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
