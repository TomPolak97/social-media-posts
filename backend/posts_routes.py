from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import logging
from datetime import datetime
from db import create_connection
from posts_routes_utils import (
    build_where_clause,
    get_order_by_clause,
    row_to_post_dict,
    get_or_create_author,
    get_next_post_id,
    build_author_update_fields,
    build_post_update_fields,
    validate_email_uniqueness,
    post_exists,
    get_post_author_id
)

router = APIRouter()

# Configure module-level logger
_logger = logging.getLogger(__name__)


# Pydantic models for request validation
class PostCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    text: str
    category: Optional[str] = None
    svg_image: Optional[str] = None
    tags: Optional[str] = None
    location: Optional[str] = None

class PostUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    text: Optional[str] = None
    category: Optional[str] = None
    svg_image: Optional[str] = None
    tags: Optional[str] = None
    location: Optional[str] = None

@router.get("/posts")
def get_posts(
    page: int = 1,
    per_page: int = 3,
    search: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    sort_by: str = "Most Recent"
):
    """
    Get posts with pagination, filtering, and sorting.
    
    Args:
        page: Page number (1-indexed)
        per_page: Number of posts per page
        search: Search term for post text or author name
        category: Filter by category
        date_from: Filter posts from this date
        date_to: Filter posts until this date
        first_name: Filter by author first name
        last_name: Filter by author last name
        sort_by: Sort option (Most Recent, Highest Engagement, Most Liked, Most Commented)
        
    Returns:
        Dictionary with posts, pagination info, and totals
        
    Raises:
        HTTPException: If database connection fails or query error occurs
    """
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Build WHERE clause and ORDER BY clause using utilities
        where_clause, params = build_where_clause(
            search=search,
            category=category,
            date_from=date_from,
            date_to=date_to,
            first_name=first_name,
            last_name=last_name
        )
        order_by = get_order_by_clause(sort_by)
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(*) 
            FROM posts p
            JOIN authors a ON p.author_id = a.id
            WHERE {where_clause}
        """
        c.execute(count_query, params)
        total = c.fetchone()[0]
        
        # Calculate pagination
        offset = (page - 1) * per_page
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        # Get paginated posts
        query = f"""
            SELECT p.id, p.text, p.post_date, p.likes, p.comments, p.shares,
                   p.total_engagements, p.engagement_rate, p.svg_image, p.category,
                   p.tags, p.location,
                   a.first_name, a.last_name, a.email, a.company, a.job_title, a.bio, a.follower_count, a.verified
            FROM posts p
            JOIN authors a ON p.author_id = a.id
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        
        c.execute(query, params)
        rows = c.fetchall()
        
        # Convert rows to post dictionaries using utility function
        posts = [row_to_post_dict(row) for row in rows]
        
        _logger.debug(f"Retrieved {len(posts)} posts (page {page}/{total_pages}, total: {total})")
        
        return {
            "posts": posts,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error fetching posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/posts/stats")
def get_posts_stats():
    """
    Get aggregate statistics for all posts (for header dashboard).
    
    Returns:
        Dictionary with total_posts, total_likes, total_comments, avg_engagement_rate
        
    Raises:
        HTTPException: If database connection fails or query error occurs
    """
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Get aggregate statistics
        c.execute("""
            SELECT 
                COUNT(*) as total_posts,
                SUM(likes) as total_likes,
                SUM(comments) as total_comments,
                AVG(engagement_rate) as avg_engagement_rate
            FROM posts
        """)
        row = c.fetchone()
        
        _logger.debug(f"Retrieved stats: {row[0]} posts, {row[1]} likes, {row[2]} comments")
        
        return {
            "total_posts": row[0] or 0,
            "total_likes": row[1] or 0,
            "total_comments": row[2] or 0,
            "avg_engagement_rate": round(float(row[3] or 0), 1)
        }
    except Exception as e:
        _logger.error(f"Error fetching stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/posts")
def create_post(post_data: PostCreate):
    """
    Create a new post with author information.
    
    If author exists (by email), updates author info if provided.
    If author doesn't exist, creates a new author.
    
    Args:
        post_data: Post creation data including author and post information
        
    Returns:
        Dictionary with created post ID and success message
        
    Raises:
        HTTPException: If database error occurs or integrity constraint violated
    """
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Get or create author using utility function
        author_id = get_or_create_author(
            cursor=c,
            email=post_data.email,
            first_name=post_data.first_name,
            last_name=post_data.last_name,
            company=post_data.company,
            job_title=post_data.job_title
        )
        
        # Get next post ID using utility function
        next_id = get_next_post_id(c)
        
        # Get current date/time
        post_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the post
        c.execute("""
            INSERT INTO posts (id, author_id, text, post_date, likes, comments, shares,
                              total_engagements, engagement_rate, svg_image, category, tags, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            next_id,
            author_id,
            post_data.text,
            post_date,
            0,  # likes
            0,  # comments
            0,  # shares
            0,  # total_engagements
            0.0,  # engagement_rate
            post_data.svg_image,
            post_data.category,
            post_data.tags,
            post_data.location
        ))
        
        conn.commit()
        _logger.info(f"Post created with ID: {next_id} for author ID: {author_id}")
        
        return {
            "id": next_id,
            "message": "Post created successfully"
        }
    except sqlite3.IntegrityError as e:
        _logger.error(f"Database integrity error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error creating post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/posts/{post_id}")
def update_post(post_id: int, post_data: PostUpdate):
    """
    Update an existing post and/or its author information.
    
    Only provided fields (not None) will be updated.
    Empty strings for optional fields will clear them (set to NULL).
    
    Args:
        post_id: ID of the post to update
        post_data: Partial post data with fields to update
        
    Returns:
        Dictionary with success message and post ID
        
    Raises:
        HTTPException: If post not found, email conflict, or database error occurs
    """
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Check if post exists and get author ID
        if not post_exists(c, post_id):
            raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found")
        
        author_id = get_post_author_id(c, post_id)
        if author_id is None:
            raise HTTPException(status_code=404, detail=f"Author not found for post {post_id}")
        
        # Get current email for validation
        c.execute("SELECT email FROM authors WHERE id = ?", (author_id,))
        current_email_row = c.fetchone()
        current_email = current_email_row[0] if current_email_row else None
        
        # Validate email uniqueness if email is being changed
        if post_data.email is not None:
            validate_email_uniqueness(c, post_data.email, author_id, current_email)
        
        # Build author update fields using utility function
        author_update_fields, author_update_values = build_author_update_fields(
            first_name=post_data.first_name,
            last_name=post_data.last_name,
            email=post_data.email,
            company=post_data.company,
            job_title=post_data.job_title
        )
        
        # Update author if there are fields to update
        if author_update_fields:
            author_update_values.append(author_id)
            c.execute(f"""
                UPDATE authors 
                SET {', '.join(author_update_fields)}
                WHERE id = ?
            """, author_update_values)
            _logger.debug(f"Updated author {author_id} with {len(author_update_fields)} field(s)")
        
        # Build post update fields using utility function
        post_update_fields, post_update_values = build_post_update_fields(
            text=post_data.text,
            category=post_data.category,
            svg_image=post_data.svg_image,
            tags=post_data.tags,
            location=post_data.location
        )
        
        # Update post if there are fields to update
        if post_update_fields:
            post_update_values.append(post_id)
            c.execute(f"""
                UPDATE posts 
                SET {', '.join(post_update_fields)}
                WHERE id = ?
            """, post_update_values)
            _logger.debug(f"Updated post {post_id} with {len(post_update_fields)} field(s)")
        
        conn.commit()
        _logger.info(f"Post {post_id} updated successfully")
        
        return {
            "message": "Post updated successfully",
            "id": post_id
        }
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error updating post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/posts/{post_id}")
def delete_post(post_id: int):
    """
    Delete a post by ID.
    
    Args:
        post_id: ID of the post to delete
        
    Returns:
        Dictionary with success message and deleted post ID
        
    Raises:
        HTTPException: If post not found or database error occurs
    """
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Check if post exists using utility function
        if not post_exists(c, post_id):
            raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found")
        
        # Delete the post
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        
        _logger.info(f"Post {post_id} deleted successfully")
        
        return {
            "message": "Post deleted successfully",
            "id": post_id
        }
    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Error deleting post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
