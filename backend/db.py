"""
Database connection and management module for SQLite.

This module provides a singleton pattern for database connections,
ensuring thread-safe access and efficient connection reuse.
"""

import sqlite3
import logging
import threading
from contextlib import contextmanager
from typing import Optional

# Configure module-level logger
_logger = logging.getLogger(__name__)

# Database configuration constants
DB_NAME = "social_media_posts.db"
DEFAULT_TIMEOUT = 5.0
WAL_MODE = "WAL"


class DatabaseConnection:
    """
    Singleton database connection manager for SQLite.
    
    Ensures thread-safe database access with automatic connection
    recovery and WAL mode for improved concurrency.
    
    Attributes:
        _instance: Class-level singleton instance
        _lock: Thread lock for synchronization
        _connection: Active SQLite connection
    """
    
    _instance: Optional['DatabaseConnection'] = None
    _lock = threading.Lock()
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls) -> 'DatabaseConnection':
        """Create or return the singleton instance (thread-safe)."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super(DatabaseConnection, cls).__new__(cls)
                    _logger.debug("DatabaseConnection singleton instance created")
        return cls._instance
    
    def get_connection(self, timeout: float = DEFAULT_TIMEOUT) -> Optional[sqlite3.Connection]:
        """
        Get or create a database connection.
        
        Uses singleton pattern to ensure only one connection exists.
        Automatically recreates connection if it was closed.
        Enables WAL mode for better concurrent access.
        
        Args:
            timeout: Timeout in seconds for database operations (default: 5.0)
        
        Returns:
            sqlite3.Connection if successful, None if connection fails
            
        Logs:
            INFO: Successful connection creation
            ERROR: Connection errors
            DEBUG: Connection state changes
        """
        with self._lock:
            if self._connection is None:
                return self._create_new_connection(timeout)
            else:
                return self._verify_and_recover_connection(timeout)
    
    def _create_new_connection(self, timeout: float) -> Optional[sqlite3.Connection]:
        """
        Create a new database connection with WAL mode enabled.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            sqlite3.Connection if successful, None otherwise
        """
        try:
            _logger.debug(f"Creating new database connection to '{DB_NAME}' (timeout: {timeout}s)")
            self._connection = sqlite3.connect(
                DB_NAME,
                timeout=timeout,
                check_same_thread=False  # Allow use from different threads
            )
            self._enable_wal_mode()
            _logger.info(f"Successfully connected to SQLite database: {DB_NAME}")
            return self._connection
        except sqlite3.Error as e:
            _logger.error(f"Failed to create database connection: {e}", exc_info=True)
            self._connection = None
            return None
    
    def _enable_wal_mode(self) -> None:
        """
        Enable Write-Ahead Logging (WAL) mode for better concurrency.
        
        WAL mode allows multiple readers and a single writer simultaneously,
        improving performance for read-heavy workloads.
        """
        try:
            self._connection.execute(f"PRAGMA journal_mode={WAL_MODE}")
            _logger.debug(f"Enabled {WAL_MODE} mode for database")
        except sqlite3.Error as e:
            _logger.warning(f"Failed to enable WAL mode: {e}")
    
    def _verify_and_recover_connection(self, timeout: float) -> Optional[sqlite3.Connection]:
        """
        Verify connection is alive and recover if needed.
        
        Args:
            timeout: Connection timeout for reconnection
            
        Returns:
            sqlite3.Connection if successful, None otherwise
        """
        if self._is_connection_alive():
            _logger.debug("Existing database connection is alive")
            return self._connection
        else:
            _logger.warning("Database connection was closed, attempting to recover...")
            return self._recover_connection(timeout)
    
    def _is_connection_alive(self) -> bool:
        """
        Check if the current connection is still valid.
        
        Returns:
            True if connection is alive, False otherwise
        """
        try:
            self._connection.execute("SELECT 1")
            return True
        except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
            _logger.debug(f"Connection health check failed: {e}")
            return False
    
    def _recover_connection(self, timeout: float) -> Optional[sqlite3.Connection]:
        """
        Recover a closed connection by creating a new one.
        
        Args:
            timeout: Connection timeout for reconnection
            
        Returns:
            sqlite3.Connection if successful, None otherwise
        """
        try:
            _logger.info("Recreating database connection...")
            self._connection = sqlite3.connect(
                DB_NAME,
                timeout=timeout,
                check_same_thread=False
            )
            self._enable_wal_mode()
            _logger.info("Successfully reconnected to SQLite database")
            return self._connection
        except sqlite3.Error as e:
            _logger.error(f"Failed to recover database connection: {e}", exc_info=True)
            self._connection = None
            return None
    
    def close_connection(self) -> None:
        """
        Close the database connection safely.
        
        Logs connection closure and handles any errors during close operation.
        """
        with self._lock:
            if self._connection is not None:
                try:
                    self._connection.close()
                    _logger.info("Database connection closed successfully")
                except sqlite3.Error as e:
                    _logger.error(f"Error closing database connection: {e}", exc_info=True)
                finally:
                    self._connection = None
                    _logger.debug("Connection reference cleared")
            else:
                _logger.debug("Attempted to close connection, but none exists")
    
    def reset_connection(self) -> Optional[sqlite3.Connection]:
        """
        Close and reset the connection, then create a new one.
        
        Useful for forcing a fresh connection when issues are suspected.
        
        Returns:
            New sqlite3.Connection if successful, None otherwise
        """
        _logger.info("Resetting database connection...")
        self.close_connection()
        return self.get_connection()


# Singleton instance - created on module import
_db_connection = DatabaseConnection()


def create_connection() -> Optional[sqlite3.Connection]:
    """
    Get or create a database connection (singleton pattern).
    
    Convenience function that maintains backward compatibility
    with existing code that uses this function signature.
    
    Returns:
        sqlite3.Connection if successful, None if connection fails
        
    Example:
        >>> conn = create_connection()
        >>> if conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
    """
    return _db_connection.get_connection()


def close_connection() -> None:
    """
    Close the database connection.
    
    Convenience function for closing the singleton connection.
    """
    _db_connection.close_connection()


def reset_connection() -> Optional[sqlite3.Connection]:
    """
    Reset the database connection (close and recreate).
    
    Returns:
        New sqlite3.Connection if successful, None otherwise
    """
    return _db_connection.reset_connection()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Provides a clean way to work with database connections that ensures
    proper resource handling. The connection is managed by the singleton,
    so it remains open after the context exits.
    
    Usage:
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM posts")
                results = cursor.fetchall()
    
    Yields:
        sqlite3.Connection or None if connection fails
    """
    conn = create_connection()
    try:
        if conn is None:
            _logger.warning("Context manager received None connection")
        yield conn
    except Exception as e:
        _logger.error(f"Error in database connection context: {e}", exc_info=True)
        raise
    finally:
        # With singleton pattern, connection stays open for reuse
        # Only log if needed for debugging
        _logger.debug("Exiting database connection context")


def create_tables() -> None:
    """
    Create database tables if they don't exist.
    
    Creates both 'authors' and 'posts' tables with appropriate
    schema, constraints, and foreign key relationships.
    
    Tables created:
        - authors: User/author information
        - posts: Social media posts with author reference
        
    Raises:
        sqlite3.Error: If table creation fails
        
    Logs:
        INFO: Successful table creation
        ERROR: Table creation failures
    """
    _logger.info("Checking database tables...")
    
    conn = create_connection()
    if conn is None:
        _logger.error("Cannot create tables: No database connection available")
        return
    
    try:
        cursor = conn.cursor()
        
        # Create authors table
        _logger.debug("Creating 'authors' table if not exists...")
        cursor.execute(_get_authors_table_schema())
        
        # Create posts table
        _logger.debug("Creating 'posts' table if not exists...")
        cursor.execute(_get_posts_table_schema())
        
        conn.commit()
        _logger.info("Database tables verified/created successfully")
        
    except sqlite3.Error as e:
        _logger.error(f"Failed to create database tables: {e}", exc_info=True)
        if conn:
            conn.rollback()
            _logger.debug("Rolled back transaction due to table creation error")
        raise


def _get_authors_table_schema() -> str:
    """
    Get the SQL schema for the authors table.
    
    Returns:
        SQL CREATE TABLE statement for authors table
    """
    return """
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
    """


def _get_posts_table_schema() -> str:
    """
    Get the SQL schema for the posts table.
    
    Returns:
        SQL CREATE TABLE statement for posts table
    """
    return """
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
    """
