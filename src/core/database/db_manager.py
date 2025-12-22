
import sqlite3
import threading
from typing import Optional
from src.utils.logger import get_logger
from src.utils.helpers import get_db_path
from migrations.runner import MigrationRunner

logger = get_logger()

class DatabaseManager:
    """
    Singleton class to manage SQLite database connection.
    Implements persistent connection to avoid filesystem overhead on every query.
    Thread-safe implementation using locking mechanism.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.db_path = get_db_path()
        self.connection: Optional[sqlite3.Connection] = None
        self._connection_lock = threading.RLock()
        self._initialized = True
        
        # Run migrations on startup
        self._run_migrations()
        
        logger.info(f"DatabaseManager initialized with path: {self.db_path}")
    
    def _run_migrations(self):
        """Auto-run pending migrations on startup"""
        try:
            runner = MigrationRunner(self.db_path)
            pending = runner.get_pending_migrations()
            
            if pending:
                logger.info(f"Checking database migrations... {len(pending)} pending.")
                if runner.migrate():
                    logger.info("Database migrations completed successfully.")
                else:
                    logger.error("Database migration failed!")
            else:
                logger.debug("Database schema is up to date.")
        except Exception as e:
            logger.error(f"Migration runner error: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns the persistent database connection.
        If connection is lost or not created, it initializes it.
        """
        with self._connection_lock:
            if self.connection is None:
                try:
                    self.connection = sqlite3.connect(
                        self.db_path, 
                        check_same_thread=False
                    )
                    # Performance optimizations
                    self.connection.execute("PRAGMA foreign_keys = ON;")
                    
                    # Create cursor to execute PRAGMA journal_mode
                    cursor = self.connection.cursor()
                    cursor.execute("PRAGMA journal_mode = WAL;")  # Write-Ahead Logging for concurrency
                    cursor.execute("PRAGMA synchronous = NORMAL;") # Faster writes, still safe
                    cursor.close()
                    
                    logger.info("New persistent database connection established (WAL mode).")
                except sqlite3.Error as e:
                    logger.error(f"Failed to connect to database: {e}")
                    raise
            return self.connection

    def _initialize_schema(self, conn: sqlite3.Connection):
        """Creates necessary tables if they don't exist."""
        try:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Face Encodings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_encodings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    encoding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    object_label TEXT,
                    confidence REAL,
                    snapshot_path TEXT,
                    identification_method TEXT DEFAULT 'unknown',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration: Add identification_method column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE events ADD COLUMN identification_method TEXT DEFAULT 'unknown'")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Re-ID Embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reid_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    vector BLOB NOT NULL,
                    confidence REAL,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Gait Embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gait_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Index for faster gait lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_gait_user ON gait_embeddings(user_id)
            """)
            
            # App Users (Login)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'operator',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)
            
            conn.commit()
            cursor.close()
        except sqlite3.Error as e:
            logger.error(f"Schema initialization failed: {e}")
            # Don't raise, as connection might still be usable or we want to retry


    def close_connection(self):
        """Closes the persistent connection."""
        with self._connection_lock:
            if self.connection:
                try:
                    self.connection.close()
                    logger.info("Database connection closed.")
                except sqlite3.Error as e:
                    logger.error(f"Error closing database: {e}")
                finally:
                    self.connection = None

    def execute_write(self, query: str, params: tuple = ()) -> bool:
        """
        Thread-safe helper for simple write operations (UPDATE/DELETE).
        Auto-commits on success.
        """
        with self._connection_lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                cursor.close()
                return True
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database write error: {e} | Query: {query}")
                return False

    def execute_many_write(self, query: str, params_list: list) -> bool:
        """
        Thread-safe helper for batch write operations using executemany.
        Faster for bulk inserts.
        """
        if not params_list:
            return True
            
        with self._connection_lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                cursor.close()
                return True
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database batch error: {e} | Query: {query}")
                return False

    def execute_insert(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        Execute INSERT and return lastrowid.
        """
        with self._connection_lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                row_id = cursor.lastrowid
                cursor.close()
                return row_id
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Database insert error: {e} | Query: {query}")
                return None

    def execute_read(self, query: str, params: tuple = ()) -> list:
        """
        Thread-safe helper for read operations.
        Returns list of tuples.
        """
        # Note: SQLite in WAL mode allows simultaneous readers.
        # We lock to ensure the connection doesn't close mid-read, 
        # but pure reads might not need full lock if we trust the connection state.
        # For safety in this shared-conn model, we lock.
        with self._connection_lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                cursor.close()
                return results
            except sqlite3.Error as e:
                logger.error(f"Database read error: {e} | Query: {query}")
                return []

    def execute_read_with_columns(self, query: str, params: tuple = ()):
        """Returns (columns_list, rows_list)."""
        with self._connection_lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                return columns, rows
            except sqlite3.Error as e:
                logger.error(f"Database read error: {e} | Query: {query}")
                return [], []

def get_db_manager() -> DatabaseManager:
    """Convenience wrapper to get the DatabaseManager singleton."""
    return DatabaseManager()
