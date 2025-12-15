# Technical Specification (FacePro v1.0)

## 1. System Architecture
The application follows a modular **Model-View-Controller (MVC)** pattern adapted for a Desktop GUI application.

### 1.1. Concurrency Model (Threading)
To prevent the GUI from freezing, the application MUST use `QThread` for all heavy operations:
* **Main Thread (UI):** Handles PyQt6 event loop, button clicks, and image rendering.
* **Camera Thread (`CameraWorker`):**
    * Connects to RTSP/Webcam using `cv2.VideoCapture`.
    * Maintains a specific FPS (e.g., 30 FPS) reading rate.
    * Handles **Auto-Reconnect** logic (if frame is None for 5 seconds, release and reconnect).
    * Emits `raw_frame_signal` to the AI Thread.
* **AI Thread (`AIWorker`):**
    * Receives frames from Camera Thread.
    * Runs the detection pipeline (Motion -> YOLO -> Face -> Re-ID).
    * Emits `processed_frame_signal` (with bounding boxes) back to Main Thread for display.

## 2. The AI Pipeline Logic (Critical)
The AI processing must follow this sequential logic to save CPU/RAM:

1.  **Motion Detection (Gatekeeper):**
    * Convert frame to Grayscale -> Gaussian Blur.
    * Calculate `cv2.absdiff` with background.
    * **IF** motion pixels < Threshold: Skip AI, return frame immediately.
    * **ELSE**: Proceed to Object Detection.

2.  **Object Detection (YOLOv8n - Quantized):**
    * Model: `yolov8n.pt` (Exported to ONNX or used with `int8` quantization if available).
    * Classes: Filter only `Person (0)`, `Cat (15)`, `Dog (16)`.
    * **IF** Person detected: Crop the person's image -> Proceed to Face/Re-ID.

3.  **Identity Resolution (Hybrid Re-ID):**
    * **Step A: Face Recognition (dlib/face_recognition):**
        * Check if face is visible and clear.
        * If Match Found (e.g., "Ali"):
            * **Passive Enrollment:** Extract the *Body Embedding* of this frame using EfficientNet-B0 and update "Ali's" profile in `reid_embeddings` table. This keeps the body model up-to-date with current clothing.
    * **Step B: Body Re-ID (If Face Failed):**
        * If face is NOT visible, extract Body Embedding.
        * Compare with stored embeddings in DB using **Cosine Similarity**.
        * Threshold: > 0.75 (Confidence).
        * If Match: Label as "Ali (Re-ID)".

## 3. Hardware & Storage Specs

### 3.1. Storage (FIFO Policy)
* **Root Path:** `./data/recordings/`
* **Logic:** A background timer (every 10 mins) checks folder size.
* **Action:** If size > `MAX_SIZE` (e.g., 5GB), delete the oldest files based on creation time (`os.path.getctime`) until size is within limits.

### 3.2. GSM Module Integration (Offline Mode)
* **Library:** `pyserial`
* **Trigger:** When `InternetCheck()` fails AND `PersonDetected()` is True.
* **Protocol:** AT Commands.
    * `AT` (Check connection)
    * `AT+CMGF=1` (Set Text Mode)
    * `AT+CMGS="+99450xxxxxxx"` (Send SMS)

## 4. Error Handling
* **RTSP Failures:** Do not crash. Log error, show "Reconnecting..." overlay on UI, and retry indefinitely.
* **Model Loading:** If GPU is missing, silently fallback to CPU mode.