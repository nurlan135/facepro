"""
FacePro Database Initialization Script
Bu skript SQLite bazasını yaradır və cədvəlləri qurur.
"""

import sqlite3
import os

def init_database():
    """SQLite database yaradır və cədvəlləri qurur."""
    
    # Database faylının yolu
    db_path = os.path.join(os.path.dirname(__file__), 'faceguard.db')
    
    # Əlaqə yaradırıq
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Users (People allowed/registered)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Face Encodings (Standard Face Rec)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_encodings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            encoding BLOB NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 3. Re-ID Embeddings (Body/Clothing Vectors)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reid_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            vector BLOB NOT NULL,
            confidence REAL,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 4. Event Logs (History displayed in UI)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            object_label TEXT,
            confidence REAL,
            snapshot_path TEXT,
            is_sent_telegram BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 5. App Users (Application login accounts - separate from face recognition users)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'operator',
            is_locked INTEGER DEFAULT 0,
            lock_until TIMESTAMP,
            failed_attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Dəyişiklikləri saxlayırıq
    conn.commit()
    conn.close()
    
    print(f"[OK] Database ugurla yaradildi: {db_path}")
    return db_path

if __name__ == "__main__":
    init_database()
