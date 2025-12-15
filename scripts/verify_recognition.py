
import os
import sys
import cv2
import pickle
import sqlite3
import numpy as np
import face_recognition

# Add specific paths to sys.path to ensure imports work if needed, 
# though we are running this as a standalone script.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

DB_PATH = os.path.join(project_root, 'data', 'db', 'faceguard.db')
FACES_DIR = os.path.join(project_root, 'data', 'faces')

def load_encodings_from_db():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.name, fe.encoding 
        FROM users u 
        JOIN face_encodings fe ON u.id = fe.user_id
    """)
    
    known_faces = {}
    rows = cursor.fetchall()
    
    for name, blob in rows:
        encoding = pickle.loads(blob)
        if name not in known_faces:
            known_faces[name] = []
        known_faces[name].append(encoding)
        
    conn.close()
    return known_faces

def verify_image(image_path, known_faces):
    print(f"\nVerifying image: {image_path}")
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not read image.")
        return False
        
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Get encoding
    encodings = face_recognition.face_encodings(rgb_image)
    if not encodings:
        print("Error: No face found in the verification image.")
        return False
        
    unknown_encoding = encodings[0]
    
    # Compare with all known faces
    print("Comparing with known faces in DB...")
    
    found_match = False
    
    for name, known_encodings_list in known_faces.items():
        # face_recognition.compare_faces returns a list of True/False
        matches = face_recognition.compare_faces(known_encodings_list, unknown_encoding, tolerance=0.6)
        
        if True in matches:
            distance = face_recognition.face_distance(known_encodings_list, unknown_encoding)[0]
            confidence = (1.0 - distance) * 100
            print(f"✅ MATCH FOUND! Name: {name}, Confidence: {confidence:.2f}%")
            found_match = True
            
            # We expect the name to be part of the filename for this test
            # e.g. "Nurlan_..." -> name "Nurlan"
            expected_name = os.path.basename(image_path).split('_')[0]
            if expected_name.lower() in name.lower():
                 print("   (Correctly matched expected person)")
            else:
                 print(f"   (Warning: Filename starts with '{expected_name}', but recognized as '{name}')")

    if not found_match:
        print("❌ NO MATCH FOUND within tolerance.")
        
    return found_match

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
        
    # 1. Load DB
    known_faces = load_encodings_from_db()
    print(f"Loaded {sum(len(v) for v in known_faces.values())} face encodings for {len(known_faces)} users.")
    
    if not known_faces:
        print("No faces in database. Please enroll a face first.")
        return

    # 2. Pick an image from data/faces/
    if not os.path.exists(FACES_DIR):
        print(f"Faces directory not found at {FACES_DIR}")
        return
        
    face_files = [f for f in os.listdir(FACES_DIR) if f.lower().endswith(('.jpg', '.png'))]
    
    if not face_files:
        print("No face images found in data/faces/ to test with.")
        return
        
    # Test with the first image found
    test_image_path = os.path.join(FACES_DIR, face_files[0])
    verify_image(test_image_path, known_faces)

if __name__ == "__main__":
    main()
