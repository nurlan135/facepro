"""
Migration script: Convert legacy pickle embeddings to numpy format.
Köhnə pickle formatındakı embedding-ləri yeni numpy formatına çevirir.

Usage: python scripts/migrate_embeddings.py
"""

import os
import sys
import pickle
import sqlite3
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.helpers import get_db_path

def migrate_reid_embeddings(cursor) -> tuple[int, int]:
    """Migrate Re-ID embeddings from pickle to numpy format."""
    migrated = 0
    failed = 0
    
    cursor.execute("SELECT id, vector FROM reid_embeddings")
    rows = cursor.fetchall()
    
    for row_id, blob in rows:
        try:
            # Check if already in numpy format (1280-dim float32 = 5120 bytes)
            if len(blob) == 5120:
                continue
            
            # Try to unpickle
            embedding = pickle.loads(blob)
            
            if isinstance(embedding, np.ndarray):
                # Convert to float32 and serialize
                new_blob = embedding.astype(np.float32).tobytes()
                cursor.execute("UPDATE reid_embeddings SET vector = ? WHERE id = ?", (new_blob, row_id))
                migrated += 1
                print(f"  Migrated Re-ID embedding {row_id}: {len(blob)} -> {len(new_blob)} bytes")
            else:
                print(f"  Skipped Re-ID embedding {row_id}: not a numpy array")
                failed += 1
                
        except Exception as e:
            print(f"  Failed Re-ID embedding {row_id}: {e}")
            failed += 1
    
    return migrated, failed


def migrate_gait_embeddings(cursor) -> tuple[int, int]:
    """Migrate Gait embeddings from pickle to numpy format."""
    migrated = 0
    failed = 0
    
    cursor.execute("SELECT id, embedding FROM gait_embeddings")
    rows = cursor.fetchall()
    
    for row_id, blob in rows:
        try:
            # Check if already in numpy format (256-dim float32 = 1024 bytes)
            if len(blob) == 1024:
                continue
            
            # Try to unpickle
            embedding = pickle.loads(blob)
            
            if isinstance(embedding, np.ndarray):
                # Convert to float32 and serialize
                new_blob = embedding.astype(np.float32).tobytes()
                cursor.execute("UPDATE gait_embeddings SET embedding = ? WHERE id = ?", (new_blob, row_id))
                migrated += 1
                print(f"  Migrated Gait embedding {row_id}: {len(blob)} -> {len(new_blob)} bytes")
            else:
                print(f"  Skipped Gait embedding {row_id}: not a numpy array")
                failed += 1
                
        except Exception as e:
            print(f"  Failed Gait embedding {row_id}: {e}")
            failed += 1
    
    return migrated, failed


def migrate_face_encodings(cursor) -> tuple[int, int]:
    """Migrate Face encodings from pickle to numpy format."""
    migrated = 0
    failed = 0
    
    cursor.execute("SELECT id, encoding FROM face_encodings")
    rows = cursor.fetchall()
    
    for row_id, blob in rows:
        try:
            # Check if already in numpy format
            # 128-dim float64 = 1024 bytes, 128-dim float32 = 512 bytes
            if len(blob) in (512, 1024):
                continue
            
            # Try to unpickle
            encoding = pickle.loads(blob)
            
            if isinstance(encoding, np.ndarray):
                # Convert to float64 (face_recognition default) and serialize
                new_blob = encoding.astype(np.float64).tobytes()
                cursor.execute("UPDATE face_encodings SET encoding = ? WHERE id = ?", (new_blob, row_id))
                migrated += 1
                print(f"  Migrated Face encoding {row_id}: {len(blob)} -> {len(new_blob)} bytes")
            else:
                print(f"  Skipped Face encoding {row_id}: not a numpy array")
                failed += 1
                
        except Exception as e:
            print(f"  Failed Face encoding {row_id}: {e}")
            failed += 1
    
    return migrated, failed


def main():
    print("=" * 60)
    print("FacePro Embedding Migration Script")
    print("Pickle -> Numpy Format")
    print("=" * 60)
    
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    print(f"\nDatabase: {db_path}")
    
    # Backup recommendation
    print("\n⚠️  BACKUP RECOMMENDATION:")
    print(f"   Copy {db_path} before proceeding!")
    
    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    total_migrated = 0
    total_failed = 0
    
    # Migrate Re-ID embeddings
    print("\n[1/3] Migrating Re-ID embeddings...")
    m, f = migrate_reid_embeddings(cursor)
    total_migrated += m
    total_failed += f
    print(f"  Result: {m} migrated, {f} failed")
    
    # Migrate Gait embeddings
    print("\n[2/3] Migrating Gait embeddings...")
    m, f = migrate_gait_embeddings(cursor)
    total_migrated += m
    total_failed += f
    print(f"  Result: {m} migrated, {f} failed")
    
    # Migrate Face encodings
    print("\n[3/3] Migrating Face encodings...")
    m, f = migrate_face_encodings(cursor)
    total_migrated += m
    total_failed += f
    print(f"  Result: {m} migrated, {f} failed")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"Migration complete!")
    print(f"  Total migrated: {total_migrated}")
    print(f"  Total failed: {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
