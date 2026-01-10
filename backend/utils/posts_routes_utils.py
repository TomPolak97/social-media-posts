"""
Utility functions for posts routes.

This module provides helper functions for building SQL queries,
processing database results, and handling author/post operations.
"""

import sqlite3
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Configure module-level logger
_logger = logging.getLogger(__name__)

# Sort options mapping
SORT_OPTIONS = {
    "Most Recent": "p.post_date DESC",
    "Highest Engagement": "p.total_engagements DESC",
    "Most Liked": "p.likes DESC",
    "Most Commented": "p.comments DESC"
}


def build_where_clause(
    search: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None
) -> Tuple[str, List[Any]]:
    """
    Build WHERE clause and parameters for post filtering.
    
    Args:
        search: Search term for post text or author name
        category: Post category filter
        date_from: Start date filter
        date_to: End date filter
        first_name: Author first name filter
        last_name: Author last name filter
        
    Returns:
        Tuple of (WHERE clause string, parameter list)
        
    Example:
        >>> clause, params = build_where_clause(search="test", category="Product")
        >>> clause
        'p.text LIKE ? AND a.first_name LIKE ? AND a.last_name LIKE ? AND p.category = ?'
    """
    where_conditions = []
    params = []
    
    if search:
        where_conditions.append("(p.text LIKE ? OR a.first_name LIKE ? OR a.last_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        _logger.debug(f"Added search filter: '{search}'")
    
    if category and category != "All Categories":
        where_conditions.append("p.category = ?")
        params.append(category)
        _logger.debug(f"Added category filter: '{category}'")
    
    if date_from:
        where_conditions.append("DATE(p.post_date) >= ?")
        params.append(date_from)
        _logger.debug(f"Added date_from filter: '{date_from}'")
    
    if date_to:
        where_conditions.append("DATE(p.post_date) <= ?")
        params.append(date_to)
        _logger.debug(f"Added date_to filter: '{date_to}'")
    
    if first_name:
        where_conditions.append("a.first_name LIKE ?")
        params.append(f"%{first_name}%")
        _logger.debug(f"Added first_name filter: '{first_name}'")
    
    if last_name:
        where_conditions.append("a.last_name LIKE ?")
        params.append(f"%{last_name}%")
        _logger.debug(f"Added last_name filter: '{last_name}'")
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    return where_clause, params


def get_order_by_clause(sort_by: str) -> str:
    """
    Get ORDER BY clause for sorting.
    
    Args:
        sort_by: Sort option name
        
    Returns:
        ORDER BY clause string
        
    Logs:
        WARNING: If invalid sort option provided
    """
    order_by = SORT_OPTIONS.get(sort_by, "p.post_date DESC")
    
    if sort_by not in SORT_OPTIONS:
        _logger.warning(f"Invalid sort option '{sort_by}', using default 'Most Recent'")
    
    _logger.debug(f"Using sort option: '{sort_by}' -> '{order_by}'")
    return order_by


def row_to_post_dict(row: Tuple) -> Dict[str, Any]:
    """
    Convert a database row to a post dictionary.
    
    Args:
        row: Database row tuple with post and author data
        
    Returns:
        Dictionary with post data and nested author object
        
    Expected row format:
        (id, text, post_date, likes, comments, shares, total_engagements,
         engagement_rate, svg_image, category, tags, location,
         first_name, last_name, email, company, job_title, bio,
         follower_count, verified)
    """
    return {
        "id": row[0],
        "text": row[1],
        "post_date": row[2],
        "likes": row[3],
        "comments": row[4],
        "shares": row[5],
        "total_engagements": row[6],
        "engagement_rate": row[7],
        "svg_image": row[8],
        "category": row[9],
        "tags": row[10],
        "location": row[11],
        "author": {
            "first_name": row[12],
            "last_name": row[13],
            "email": row[14],
            "company": row[15],
            "job_title": row[16],
            "bio": row[17],
            "follower_count": row[18],
            "verified": bool(row[19])
        }
    }


def get_or_create_author(
    cursor,
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None
) -> int:
    """
    Get existing author ID or create new author.
    
    Args:
        cursor: Database cursor
        email: Author email (required, used as unique identifier)
        first_name: Author first name
        last_name: Author last name
        company: Author company
        job_title: Author job title
        
    Returns:
        Author ID
        
    Logs:
        DEBUG: Author creation/update operations
        ERROR: Database errors
    """
    # Check if author exists
    cursor.execute("SELECT id FROM authors WHERE email = ?", (email,))
    author_row = cursor.fetchone()
    
    if author_row:
        author_id = author_row[0]
        _logger.debug(f"Found existing author with ID {author_id} for email: {email}")
        
        # Update author info if provided
        update_fields = []
        update_values = []
        
        if first_name:
            update_fields.append("first_name = ?")
            update_values.append(first_name)
        if last_name:
            update_fields.append("last_name = ?")
            update_values.append(last_name)
        if company:
            update_fields.append("company = ?")
            update_values.append(company)
        if job_title:
            update_fields.append("job_title = ?")
            update_values.append(job_title)
        
        if update_fields:
            update_values.append(author_id)
            cursor.execute(f"""
                UPDATE authors 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, update_values)
            _logger.debug(f"Updated author {author_id} with new information")
        
        return author_id
    else:
        # Create new author
        _logger.debug(f"Creating new author for email: {email}")
        cursor.execute("""
            INSERT INTO authors (first_name, last_name, email, company, job_title, bio, follower_count, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            first_name or "",
            last_name or "",
            email,
            company,
            job_title,
            "",
            0,
            True
        ))
        author_id = cursor.lastrowid
        _logger.info(f"Created new author with ID {author_id} for email: {email}")
        return author_id


def get_next_post_id(cursor) -> int:
    """
    Get the next available post ID.
    
    Args:
        cursor: Database cursor
        
    Returns:
        Next post ID (max existing ID + 1, or 1 if no posts exist)
    """
    cursor.execute("SELECT MAX(id) FROM posts")
    max_id_result = cursor.fetchone()
    next_id = (max_id_result[0] or 0) + 1
    _logger.debug(f"Generated next post ID: {next_id}")
    return next_id


def build_author_update_fields(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    company: Optional[str] = None,
    job_title: Optional[str] = None
) -> Tuple[List[str], List[Any]]:
    """
    Build UPDATE fields and values for author update.
    
    Args:
        first_name: New first name (None = don't update)
        last_name: New last name (None = don't update)
        email: New email (None = don't update)
        company: New company (None = don't update, empty string = clear)
        job_title: New job title (None = don't update, empty string = clear)
        
    Returns:
        Tuple of (field list, value list)
    """
    update_fields = []
    update_values = []
    
    if first_name is not None:
        update_fields.append("first_name = ?")
        update_values.append(first_name)
    
    if last_name is not None:
        update_fields.append("last_name = ?")
        update_values.append(last_name)
    
    if email is not None:
        update_fields.append("email = ?")
        update_values.append(email)
    
    if company is not None:
        update_fields.append("company = ?")
        # Empty string means clear the field (set to NULL)
        update_values.append(company if company else None)
    
    if job_title is not None:
        update_fields.append("job_title = ?")
        # Empty string means clear the field (set to NULL)
        update_values.append(job_title if job_title else None)
    
    return update_fields, update_values


def build_post_update_fields(
    text: Optional[str] = None,
    category: Optional[str] = None,
    svg_image: Optional[str] = None,
    tags: Optional[str] = None,
    location: Optional[str] = None
) -> Tuple[List[str], List[Any]]:
    """
    Build UPDATE fields and values for post update.
    
    Args:
        text: New post text (None = don't update)
        category: New category (None = don't update, empty string = clear)
        svg_image: New SVG image (None = don't update, empty string = clear)
        tags: New tags (None = don't update, empty string = clear)
        location: New location (None = don't update, empty string = clear)
        
    Returns:
        Tuple of (field list, value list)
    """
    update_fields = []
    update_values = []
    
    if text is not None:
        update_fields.append("text = ?")
        update_values.append(text)
    
    if category is not None:
        update_fields.append("category = ?")
        # Empty string means clear the field (set to NULL)
        update_values.append(category if category else None)
    
    if svg_image is not None:
        update_fields.append("svg_image = ?")
        # Empty string means clear the field (set to NULL)
        update_values.append(svg_image if svg_image else None)
    
    if tags is not None:
        update_fields.append("tags = ?")
        # Empty string means clear the field (set to NULL)
        update_values.append(tags if tags else None)
    
    if location is not None:
        update_fields.append("location = ?")
        # Empty string means clear the field (set to NULL)
        update_values.append(location if location else None)
    
    return update_fields, update_values


def validate_email_uniqueness(
    cursor,
    email: str,
    author_id: int,
    current_email: Optional[str] = None
) -> None:
    """
    Validate that email is unique (not used by another author).
    
    Args:
        cursor: Database cursor
        email: Email to validate
        author_id: Current author ID (to exclude from check)
        current_email: Current email (to skip check if unchanged)
        
    Raises:
        HTTPException: If email is already in use by another author
    """
    # Skip validation if email hasn't changed
    if current_email and current_email == email:
        _logger.debug(f"Email unchanged for author {author_id}, skipping uniqueness check")
        return
    
    cursor.execute("SELECT id FROM authors WHERE email = ? AND id != ?", (email, author_id))
    if cursor.fetchone():
        _logger.warning(f"Email '{email}' is already in use by another author")
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Email already exists for another author")
    
    _logger.debug(f"Email '{email}' is unique for author {author_id}")


def get_post_by_id(cursor, post_id: int) -> Optional[Tuple]:
    """
    Get post by ID with author information.
    
    Args:
        cursor: Database cursor
        post_id: Post ID to retrieve
        
    Returns:
        Post row tuple or None if not found
    """
    cursor.execute("""
        SELECT p.id, p.text, p.post_date, p.likes, p.comments, p.shares,
               p.total_engagements, p.engagement_rate, p.svg_image, p.category,
               p.tags, p.location,
               a.first_name, a.last_name, a.email, a.company, a.job_title, a.bio, a.follower_count, a.verified
        FROM posts p
        JOIN authors a ON p.author_id = a.id
        WHERE p.id = ?
    """, (post_id,))
    return cursor.fetchone()


def post_exists(cursor, post_id: int) -> bool:
    """
    Check if a post exists.
    
    Args:
        cursor: Database cursor
        post_id: Post ID to check
        
    Returns:
        True if post exists, False otherwise
    """
    cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
    return cursor.fetchone() is not None


def get_post_author_id(cursor, post_id: int) -> Optional[int]:
    """
    Get the author ID for a post.
    
    Args:
        cursor: Database cursor
        post_id: Post ID
        
    Returns:
        Author ID or None if post not found
    """
    cursor.execute("SELECT author_id FROM posts WHERE id = ?", (post_id,))
    result = cursor.fetchone()
    return result[0] if result else None
