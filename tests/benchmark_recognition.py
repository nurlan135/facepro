
import time
import numpy as np
import cv2
import sys
import os

# Adjust path to find src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logger import get_logger

logger = get_logger()

def benchmark_dlib():
    print("\n--- Benchmarking Dlib (face_recognition) ---")
    try:
        import face_recognition
        
        # 1. Load Dummy Image (1080p)
        img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        # 2. Face Detection Speed
        start = time.time()
        # Using HOG model (CPU default)
        locs = face_recognition.face_locations(img, model="hog") 
        duration = time.time() - start
        print(f"Detection (1080p, CPU, HOG): {duration:.4f} sec")
        
        # 3. Encoding Speed (Simulated bbox)
        # Using a dummy face crops
        face_crop = np.random.randint(0, 255, (150, 150, 3), dtype=np.uint8)
        # We need to detect face in crop first for dlib usually, but let's try direct encoding
        # face_recognition.face_encodings expects full image + locations
        
        start = time.time()
        # Sending 1 face location covering the crop
        encs = face_recognition.face_encodings(face_crop, [(0, 150, 150, 0)])
        duration = time.time() - start
        print(f"Encoding (1 Face): {duration:.4f} sec")
        
    except ImportError:
        print("face_recognition not installed/found.")
    except Exception as e:
        print(f"Dlib Benchmark Error: {e}")

def benchmark_insightface():
    print("\n--- Benchmarking InsightFace (ONNX) ---")
    try:
        import insightface
        from insightface.app import FaceAnalysis
        
        # 1. Initialization Speed
        start = time.time()
        # buffalo_l is the default model pack
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0, det_size=(640, 640))
        init_time = time.time() - start
        print(f"Initialization (CPU): {init_time:.4f} sec")
        
        # 2. Inference (Detection + Encoding)
        img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        
        start = time.time()
        faces = app.get(img)
        duration = time.time() - start
        print(f"Inference (Det + Enc) (1080p, CPU): {duration:.4f} sec")
        
    except ImportError:
        print("InsightFace not installed. Run 'pip install insightface onnxruntime'")
    except Exception as e:
        print(f"InsightFace Benchmark Error: {e}")

if __name__ == "__main__":
    print("FacePro Recognition Benchmark Tool")
    benchmark_dlib()
    benchmark_insightface()
