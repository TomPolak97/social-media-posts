"""
CSV import module for social media posts data.

This module handles importing CSV data into SQLite database,
including data cleaning, validation, and bulk insertion for performance.
"""

import pandas as pd
import os
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from db import create_connection

# Configure module-level logger
_logger = logging.getLogger(__name__)

# Configuration constants
CSV_FILE = "social_media_posts_data.csv"
BATCH_SIZE = 1000
PROGRESS_LOG_INTERVAL = 10  # Log progress every N batches

# Column name constants
NUMERIC_COLUMNS = [
    "author_follower_count",
    "likes",
    "comments",
    "shares",
    "total_engagements",
    "engagement_rate"
]

TEXT_COLUMNS = [
    "author_first_name",
    "author_last_name",
    "author_email",
    "author_company",
    "author_job_title",
    "author_bio",
    "post_text",
    "post_image_svg",
    "post_category",
    "post_tags",
    "location"
]


def import_csv() -> None:
    """
    Main function to import CSV data into SQLite database.
    
    Performs the following steps:
    1. Validates CSV file exists
    2. Reads and cleans CSV data
    3. Normalizes columns and data types
    4. Bulk inserts authors
    5. Bulk inserts posts in batches
    
    Logs:
        INFO: Successful import completion
        WARNING: Missing columns, skipped rows
        ERROR: Import failures
    """
    if not _csv_file_exists():
        return
    
    conn = None
    try:
        _logger.info(f"Starting CSV import from '{CSV_FILE}'...")
        
        # Read and clean CSV
        dataframe = _read_and_clean_csv()
        if dataframe is None or dataframe.empty:
            _logger.warning("CSV file is empty or could not be read")
            return
        
        _logger.info(f"CSV loaded successfully: {len(dataframe)} rows, {len(dataframe.columns)} columns")
        
        # Normalize data
        _normalize_dataframe_columns(dataframe)
        
        # Get database connection
        conn = create_connection()
        if conn is None:
            _logger.error("Cannot import CSV: No database connection available")
            return
        
        cursor = conn.cursor()
        
        # Process and insert authors
        author_count = _import_authors(dataframe, cursor, conn)
        
        # Map emails to author IDs
        author_map = _build_author_id_map(cursor)
        _logger.debug(f"Built author ID map with {len(author_map)} authors")
        
        # Process and insert posts
        post_count = _import_posts(dataframe, author_map, cursor, conn)
        
        _logger.info(
            f"CSV import completed successfully! "
            f"Inserted {post_count} posts and {author_count} authors"
        )
        
    except Exception as e:
        _logger.error(f"Error importing CSV: {e}", exc_info=True)
        if conn:
            conn.rollback()
            _logger.debug("Rolled back transaction due to import error")
    finally:
        # Note: We don't close connection here as it's a singleton
        # The connection manager handles connection lifecycle
        pass


def _csv_file_exists() -> bool:
    """
    Check if the CSV file exists.
    
    Returns:
        True if file exists, False otherwise
        
    Logs:
        WARNING: If file not found
    """
    if not os.path.exists(CSV_FILE):
        _logger.warning(f"CSV file not found: {CSV_FILE}")
        return False
    return True


def _read_and_clean_csv() -> Optional[pd.DataFrame]:
    """
    Read CSV file and clean column names.
    
    Returns:
        Cleaned pandas DataFrame or None if read fails
        
    Logs:
        INFO: Successful read
        DEBUG: Column names after cleaning
        ERROR: Read failures
    """
    try:
        dataframe = pd.read_csv(CSV_FILE)
        
        # Trim whitespace from column names
        dataframe.columns = dataframe.columns.str.strip()
        _logger.debug(f"Trimmed column names. Found columns: {list(dataframe.columns)}")
        
        return dataframe
        
    except Exception as e:
        _logger.error(f"Failed to read CSV file '{CSV_FILE}': {e}", exc_info=True)
        return None


def _normalize_dataframe_columns(dataframe: pd.DataFrame) -> None:
    """
    Normalize and clean all columns in the dataframe.
    
    Handles:
    - Numeric columns (conversion, default values)
    - Text columns (missing values, defaults)
    - Required columns (post_id, author_verified, post_date)
    
    Args:
        dataframe: The pandas DataFrame to normalize
        
    Logs:
        WARNING: Missing columns, using defaults
        DEBUG: Column normalization details
    """
    _logger.debug("Normalizing dataframe columns...")
    
    _normalize_numeric_columns(dataframe)
    _normalize_text_columns(dataframe)
    _ensure_required_columns(dataframe)
    _normalize_date_columns(dataframe)
    _normalize_boolean_columns(dataframe)
    
    _logger.debug("Dataframe normalization completed")


def _normalize_numeric_columns(dataframe: pd.DataFrame) -> None:
    """
    Normalize numeric columns by converting to numeric type.
    
    Args:
        dataframe: The pandas DataFrame to normalize
    """
    for column in NUMERIC_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").fillna(0)
            _logger.debug(f"Normalized numeric column '{column}'")
        else:
            dataframe[column] = 0
            _logger.warning(f"Column '{column}' not found, using default value 0")


def _normalize_text_columns(dataframe: pd.DataFrame) -> None:
    """
    Normalize text columns by filling missing values.
    
    Args:
        dataframe: The pandas DataFrame to normalize
    """
    for column in TEXT_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].fillna("")
        else:
            dataframe[column] = ""
            _logger.warning(f"Column '{column}' not found, using empty string default")


def _ensure_required_columns(dataframe: pd.DataFrame) -> None:
    """
    Ensure required columns exist, creating them with defaults if missing.
    
    Args:
        dataframe: The pandas DataFrame to validate
    """
    if "post_id" not in dataframe.columns:
        dataframe["post_id"] = range(1, len(dataframe) + 1)
        _logger.warning("Column 'post_id' not found, generating sequential IDs")
    
    if "author_follower_count" not in dataframe.columns:
        dataframe["author_follower_count"] = 0
        _logger.warning("Column 'author_follower_count' not found, using 0 default")


def _normalize_date_columns(dataframe: pd.DataFrame) -> None:
    """
    Normalize date columns, defaulting to current timestamp if missing.
    
    Args:
        dataframe: The pandas DataFrame to normalize
    """
    if "post_date" in dataframe.columns:
        dataframe["post_date"] = pd.to_datetime(
            dataframe["post_date"],
            errors="coerce"
        ).fillna(pd.Timestamp.now()).astype(str)
    else:
        current_date = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        dataframe["post_date"] = current_date
        _logger.warning(f"Column 'post_date' not found, using current date: {current_date}")


def _normalize_boolean_columns(dataframe: pd.DataFrame) -> None:
    """
    Normalize boolean columns, defaulting to False if missing.
    
    Args:
        dataframe: The pandas DataFrame to normalize
    """
    if "author_verified" in dataframe.columns:
        dataframe["author_verified"] = dataframe["author_verified"].apply(
            lambda x: bool(x) if pd.notnull(x) else False
        )
    else:
        dataframe["author_verified"] = False
        _logger.warning("Column 'author_verified' not found, using False default")


def _extract_unique_authors(dataframe: pd.DataFrame) -> Dict[str, Tuple]:
    """
    Extract unique authors from dataframe.
    
    Args:
        dataframe: The pandas DataFrame containing author data
        
    Returns:
        Dictionary mapping email to author tuple:
        (first_name, last_name, email, company, job_title, bio, follower_count, verified)
        
    Logs:
        DEBUG: Number of unique authors found
        ERROR: Row processing errors
    """
    unique_authors = {}
    skipped_rows = 0
    
    for idx, row in dataframe.iterrows():
        try:
            email = row.get("author_email", "")
            
            # Skip if email is missing, invalid, or already processed
            if not email or pd.isna(email) or email in unique_authors:
                continue
            
            # Extract author data
            author_data = _extract_author_data(row)
            if author_data:
                unique_authors[email] = author_data
                
        except (KeyError, ValueError) as e:
            _logger.error(f"Failed to process author in row {idx}: {e}")
            skipped_rows += 1
            continue
    
    if skipped_rows > 0:
        _logger.warning(f"Skipped {skipped_rows} rows during author extraction")
    
    _logger.debug(f"Extracted {len(unique_authors)} unique authors from CSV")
    return unique_authors


def _extract_author_data(row: pd.Series) -> Optional[Tuple]:
    """
    Extract author data from a dataframe row.
    
    Args:
        row: A pandas Series representing one row
        
    Returns:
        Tuple of (first_name, last_name, email, company, job_title, bio, follower_count, verified)
        or None if extraction fails
    """
    try:
        first_name = row["author_first_name"] if pd.notna(row["author_first_name"]) else ""
        last_name = row["author_last_name"] if pd.notna(row["author_last_name"]) else ""
        email = row["author_email"]
        company = row["author_company"] if pd.notna(row["author_company"]) else None
        job_title = row["author_job_title"] if pd.notna(row["author_job_title"]) else None
        bio = row["author_bio"] if pd.notna(row["author_bio"]) else ""
        follower_count = int(row["author_follower_count"]) if pd.notna(row["author_follower_count"]) else 0
        verified = bool(row["author_verified"]) if pd.notna(row["author_verified"]) else False
        
        return (first_name, last_name, email, company, job_title, bio, follower_count, verified)
    except Exception as e:
        _logger.error(f"Error extracting author data: {e}")
        return None


def _import_authors(dataframe: pd.DataFrame, cursor, conn) -> int:
    """
    Extract and bulk insert unique authors.
    
    Args:
        dataframe: The pandas DataFrame containing author data
        cursor: Database cursor
        conn: Database connection
        
    Returns:
        Number of authors inserted
        
    Logs:
        INFO: Bulk insert progress
        ERROR: Insert failures
    """
    _logger.info("Extracting unique authors...")
    unique_authors = _extract_unique_authors(dataframe)
    
    if not unique_authors:
        _logger.warning("No authors to insert from CSV")
        return 0
    
    try:
        author_values = list(unique_authors.values())
        cursor.executemany("""
            INSERT OR IGNORE INTO authors 
            (first_name, last_name, email, company, job_title, bio, follower_count, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, author_values)
        
        conn.commit()
        inserted_count = len(author_values)
        _logger.info(f"Successfully inserted {inserted_count} unique authors")
        
        return inserted_count
        
    except Exception as e:
        _logger.error(f"Failed to bulk insert authors: {e}", exc_info=True)
        conn.rollback()
        return 0


def _build_author_id_map(cursor) -> Dict[str, int]:
    """
    Build a mapping from email to author ID.
    
    Args:
        cursor: Database cursor
        
    Returns:
        Dictionary mapping email to author_id
    """
    cursor.execute("SELECT id, email FROM authors")
    return {email: author_id for author_id, email in cursor.fetchall()}


def _prepare_post_data(dataframe: pd.DataFrame, author_map: Dict[str, int]) -> List[Tuple]:
    """
    Prepare post data from dataframe for bulk insertion.
    
    Args:
        dataframe: The pandas DataFrame containing post data
        author_map: Dictionary mapping email to author_id
        
    Returns:
        List of tuples ready for bulk insert:
        (post_id, author_id, text, post_date, likes, comments, shares,
         total_engagements, engagement_rate, svg_image, category, tags, location)
        
    Logs:
        WARNING: Skipped posts (missing author, invalid ID)
        ERROR: Row processing errors
    """
    post_data = []
    skipped_posts = 0
    missing_author_count = 0
    
    for idx, row in dataframe.iterrows():
        try:
            # Get author ID
            email = row.get("author_email", "")
            author_id = author_map.get(email)
            
            if not author_id:
                missing_author_count += 1
                continue
            
            # Validate post ID
            post_id = int(row["post_id"]) if pd.notna(row["post_id"]) else 0
            if not post_id:
                skipped_posts += 1
                _logger.warning(f"Row {idx}: Invalid post_id, skipping")
                continue
            
            # Extract post data
            post_tuple = _extract_post_data(row, post_id, author_id)
            if post_tuple:
                post_data.append(post_tuple)
                
        except (KeyError, ValueError) as e:
            _logger.error(f"Failed to process post in row {idx}: {e}")
            skipped_posts += 1
            continue
    
    if skipped_posts > 0:
        _logger.warning(f"Skipped {skipped_posts} posts during data preparation")
    if missing_author_count > 0:
        _logger.warning(f"Skipped {missing_author_count} posts due to missing author mapping")
    
    _logger.debug(f"Prepared {len(post_data)} posts for insertion")
    return post_data


def _extract_post_data(row: pd.Series, post_id: int, author_id: int) -> Optional[Tuple]:
    """
    Extract post data from a dataframe row.
    
    Args:
        row: A pandas Series representing one row
        post_id: The post ID
        author_id: The author ID
        
    Returns:
        Tuple ready for database insertion or None if extraction fails
    """
    try:
        post_text = row["post_text"] if pd.notna(row["post_text"]) else ""
        post_date = row["post_date"] if pd.notna(row["post_date"]) else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        likes = int(row["likes"]) if pd.notna(row["likes"]) else 0
        comments = int(row["comments"]) if pd.notna(row["comments"]) else 0
        shares = int(row["shares"]) if pd.notna(row["shares"]) else 0
        total_engagements = int(row["total_engagements"]) if pd.notna(row["total_engagements"]) else 0
        engagement_rate = float(row["engagement_rate"]) if pd.notna(row["engagement_rate"]) else 0.0
        svg_image = row["post_image_svg"] if pd.notna(row["post_image_svg"]) else None
        category = row["post_category"] if pd.notna(row["post_category"]) else None
        tags = row["post_tags"] if pd.notna(row["post_tags"]) else None
        location = row["location"] if pd.notna(row["location"]) else None
        
        return (
            post_id,
            author_id,
            post_text,
            post_date,
            likes,
            comments,
            shares,
            total_engagements,
            engagement_rate,
            svg_image,
            category,
            tags,
            location
        )
    except Exception as e:
        _logger.error(f"Error extracting post data: {e}")
        return None


def _import_posts(
    dataframe: pd.DataFrame,
    author_map: Dict[str, int],
    cursor,
    conn
) -> int:
    """
    Prepare and bulk insert posts in batches.
    
    Args:
        dataframe: The pandas DataFrame containing post data
        author_map: Dictionary mapping email to author_id
        cursor: Database cursor
        conn: Database connection
        
    Returns:
        Number of posts inserted
        
    Logs:
        INFO: Batch insertion progress
        ERROR: Insert failures
    """
    _logger.info("Preparing posts for bulk insertion...")
    post_data = _prepare_post_data(dataframe, author_map)
    
    if not post_data:
        _logger.warning("No posts to insert from CSV")
        return 0
    
    try:
        total_inserted = _bulk_insert_posts_in_batches(post_data, cursor, conn)
        _logger.info(f"Successfully inserted {total_inserted} posts")
        
        return total_inserted
        
    except Exception as e:
        _logger.error(f"Failed to bulk insert posts: {e}", exc_info=True)
        conn.rollback()
        return 0


def _bulk_insert_posts_in_batches(
    post_data: List[Tuple],
    cursor,
    conn
) -> int:
    """
    Insert posts in batches for better memory management and progress tracking.
    
    Args:
        post_data: List of post tuples ready for insertion
        cursor: Database cursor
        conn: Database connection
        
    Returns:
        Total number of posts inserted
        
    Logs:
        INFO: Progress updates during batch insertion
    """
    total_inserted = 0
    total_batches = (len(post_data) + BATCH_SIZE - 1) // BATCH_SIZE
    
    _logger.info(f"Inserting {len(post_data)} posts in {total_batches} batches (batch size: {BATCH_SIZE})...")
    
    for batch_num, i in enumerate(range(0, len(post_data), BATCH_SIZE), 1):
        batch = post_data[i:i + BATCH_SIZE]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO posts 
            (id, author_id, text, post_date, likes, comments, shares,
             total_engagements, engagement_rate, svg_image, category, tags, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        
        total_inserted += len(batch)
        
        # Log progress periodically
        if batch_num % PROGRESS_LOG_INTERVAL == 0 or batch_num == total_batches:
            _logger.info(f"Progress: Inserted {total_inserted}/{len(post_data)} posts ({batch_num}/{total_batches} batches)")
    
    conn.commit()
    _logger.debug(f"Completed batch insertion: {total_inserted} posts inserted")
    
    return total_inserted
