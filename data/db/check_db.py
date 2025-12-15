import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'faceguard.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("Tables:", tables)

# Check each table structure
for table in tables:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"\n{table}:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()
