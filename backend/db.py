import sqlite3
import logging
import threading
from contextlib import contextmanager

DB_NAME = "social_media_posts.db"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class DatabaseConnection:
    """Singleton database connection manager for SQLite"""
    _instance = None
    _lock = threading.Lock()
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def get_connection(self, timeout=5.0):
        """
        Get or create a database connection.
        Uses a singleton pattern to ensure only one connection exists.
        Automatically recreates connection if it was closed.
        
        Args:
            timeout: Timeout in seconds for database operations (helps with locking)
        
        Returns:
            sqlite3.Connection or None if connection fails
        """
        with self._lock:
            # Check if connection exists and is still open
            if self._connection is None:
                try:
                    # Enable WAL mode for better concurrency
                    self._connection = sqlite3.connect(
                        DB_NAME,
                        timeout=timeout,
                        check_same_thread=False  # Allow use from different threads
                    )
                    # Enable WAL mode for better concurrent access
                    self._connection.execute("PRAGMA journal_mode=WAL")
                    logging.info("Connected to SQLite database")
                except sqlite3.Error as e:
                    logging.error(f"SQLite connection error: {e}")
                    return None
            else:
                # Check if connection is still open (closed connections raise error on execute)
                try:
                    self._connection.execute("SELECT 1")
                except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                    # Connection was closed, recreate it
                    logging.info("Connection was closed, recreating...")
                    try:
                        self._connection = sqlite3.connect(
                            DB_NAME,
                            timeout=timeout,
                            check_same_thread=False
                        )
                        self._connection.execute("PRAGMA journal_mode=WAL")
                        logging.info("Reconnected to SQLite database")
                    except sqlite3.Error as e:
                        logging.error(f"SQLite reconnection error: {e}")
                        self._connection = None
                        return None
            return self._connection
    
    def close_connection(self):
        """Close the database connection"""
        with self._lock:
            if self._connection is not None:
                try:
                    self._connection.close()
                    logging.info("Database connection closed")
                except sqlite3.Error as e:
                    logging.error(f"Error closing connection: {e}")
                finally:
                    self._connection = None
    
    def reset_connection(self):
        """Close and reset the connection (useful for reconnection)"""
        self.close_connection()
        return self.get_connection()


# Singleton instance
_db_connection = DatabaseConnection()


def create_connection():
    """
    Get or create a database connection (singleton pattern).
    For backward compatibility, maintains the same function signature.
    
    Returns:
        sqlite3.Connection or None if connection fails
    """
    return _db_connection.get_connection()


def close_connection():
    """Close the database connection"""
    _db_connection.close_connection()


def reset_connection():
    """Reset the database connection"""
    return _db_connection.reset_connection()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper connection handling with the singleton pattern.
    
    Usage:
        with get_db_connection() as conn:
            # use conn
            pass
    """
    conn = create_connection()
    try:
        yield conn
    finally:
        # With singleton, we typically don't close, but this allows explicit control
        pass


def create_tables():
    """Create authors and posts tables if not exists"""
    try:
        conn = create_connection()
        if conn is None:
            logging.error("No connection available. Cannot create tables.")
            return
        c = conn.cursor()

        # Authors table
        c.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            company TEXT,
            job_title TEXT,
            bio TEXT,
            follower_count INTEGER,
            verified BOOLEAN
        )
        """)

        # Posts table
        c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            author_id INTEGER,
            text TEXT,
            post_date TEXT,
            likes INTEGER,
            comments INTEGER,
            shares INTEGER,
            total_engagements INTEGER,
            engagement_rate REAL,
            svg_image TEXT,
            category TEXT,
            tags TEXT,
            location TEXT,
            FOREIGN KEY (author_id) REFERENCES authors(id)
        )
        """)

        conn.commit()
        logging.info("Tables created or already exist")
    except sqlite3.Error as e:
        logging.error(f"Error creating tables: {e}")
    # Don't close connection here - it's a singleton and should stay open
