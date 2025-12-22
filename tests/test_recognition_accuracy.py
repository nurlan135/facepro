"""
InsightFace Recognition Accuracy Test
======================================
Tests if the enrolled faces can be correctly recognized.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import numpy as np
from pathlib import Path

from src.core.face_recognizer import FaceRecognizer
from src.core.database.db_manager import DatabaseManager
from src.core.database.repositories.embedding_repository import EmbeddingRepository
from src.utils.logger import get_logger

logger = get_logger()


def load_known_faces(db_manager: DatabaseManager):
    """Load all enrolled face embeddings from database."""
    # Get all users with their embeddings directly
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.name, fe.encoding 
        FROM users u 
        JOIN face_encodings fe ON u.id = fe.user_id
    """)
    rows = cursor.fetchall()
    
    known_faces = []
    for user_id, name, encoding_blob in rows:
        # Decode embedding (512d for InsightFace, 128d for dlib)
        embedding = np.frombuffer(encoding_blob, dtype=np.float32)
        known_faces.append({
            'user_id': user_id,
            'name': name,
            'embedding': embedding,
            'dim': len(embedding)
        })
        print(f"  Loaded: {name} ({len(embedding)}d vector)")
    
    return known_faces


def test_recognition(test_image_path: str, known_faces: list, recognizer: FaceRecognizer):
    """Test recognition on a single image."""
    print(f"\n  Testing: {os.path.basename(test_image_path)}")
    
    # Load image (BGR format for OpenCV)
    img = cv2.imread(test_image_path)
    if img is None:
        print(f"    ERROR: Could not load image")
        return None
    
    # Get embedding using FaceRecognizer's method
    test_embedding = recognizer.get_embedding_for_image(img)
    
    if test_embedding is None:
        print(f"    WARNING: No face detected or could not extract embedding")
        return None
    
    print(f"    Extracted {len(test_embedding)}d embedding")
    
    # Compare with all known faces
    best_match = None
    best_score = -1
    
    for known in known_faces:
        if len(known['embedding']) != len(test_embedding):
            print(f"    SKIP: Dimension mismatch ({known['name']}: {known['dim']}d vs test: {len(test_embedding)}d)")
            continue
        
        # Cosine similarity for InsightFace
        similarity = np.dot(test_embedding, known['embedding']) / (
            np.linalg.norm(test_embedding) * np.linalg.norm(known['embedding'])
        )
        
        print(f"    vs {known['name']}: {similarity:.4f} similarity")
        
        if similarity > best_score:
            best_score = similarity
            best_match = known['name']
    
    return {
        'best_match': best_match,
        'score': best_score,
        'threshold': 0.4  # InsightFace recommended threshold
    }


def main():
    print("=" * 60)
    print("InsightFace Recognition Accuracy Test")
    print("=" * 60)
    
    # Initialize
    db_path = Path(__file__).parent.parent / "data" / "db" / "facepro.db"
    db_manager = DatabaseManager()
    
    recognizer = FaceRecognizer(backend='insightface')
    print(f"\nBackend: {recognizer.backend}")
    print(f"Embedding dimension: {recognizer.embedding_dim}d")
    
    # Load known faces
    print("\n[1] Loading enrolled faces from database...")
    known_faces = load_known_faces(db_manager)
    
    if not known_faces:
        print("ERROR: No enrolled faces found in database!")
        return
    
    # Find test images
    print("\n[2] Finding test images...")
    faces_dir = Path(__file__).parent.parent / "data" / "faces"
    test_images = list(faces_dir.rglob("*.jpg")) + list(faces_dir.rglob("*.png"))
    
    print(f"  Found {len(test_images)} images to test")
    
    # Test each image
    print("\n[3] Running recognition tests...")
    results = []
    
    for img_path in test_images:
        # Extract expected name from path
        expected_name = img_path.parent.name if img_path.parent.name != "faces" else img_path.stem.split("_")[0]
        
        result = test_recognition(str(img_path), known_faces, recognizer)
        
        if result:
            is_correct = result['best_match'] == expected_name
            is_above_threshold = result['score'] >= result['threshold']
            
            results.append({
                'image': img_path.name,
                'expected': expected_name,
                'predicted': result['best_match'],
                'score': result['score'],
                'correct': is_correct,
                'confident': is_above_threshold
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    if results:
        correct = sum(1 for r in results if r['correct'] and r['confident'])
        total = len(results)
        accuracy = (correct / total) * 100
        
        print(f"\nAccuracy: {correct}/{total} ({accuracy:.1f}%)")
        print(f"\nDetails:")
        for r in results:
            status = "OK" if r['correct'] and r['confident'] else "FAIL"
            print(f"  [{status}] {r['image']}: expected={r['expected']}, got={r['predicted']} (score={r['score']:.4f})")
    else:
        print("No valid results to report.")
    
    db_manager.close()


if __name__ == "__main__":
    main()
