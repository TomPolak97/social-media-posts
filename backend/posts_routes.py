from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import logging
from datetime import datetime
from db import create_connection

router = APIRouter()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


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
    """Get posts with pagination, filtering, and sorting - direct SQLite query"""
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Build WHERE clause for filtering
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("(p.text LIKE ? OR a.first_name LIKE ? OR a.last_name LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        if category and category != "All Categories":
            where_conditions.append("p.category = ?")
            params.append(category)
        
        if date_from:
            where_conditions.append("DATE(p.post_date) >= ?")
            params.append(date_from)
        
        if date_to:
            where_conditions.append("DATE(p.post_date) <= ?")
            params.append(date_to)
        
        if first_name:
            where_conditions.append("a.first_name LIKE ?")
            params.append(f"%{first_name}%")
        
        if last_name:
            where_conditions.append("a.last_name LIKE ?")
            params.append(f"%{last_name}%")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build ORDER BY clause
        order_by = {
            "Most Recent": "p.post_date DESC",
            "Highest Engagement": "p.total_engagements DESC",
            "Most Liked": "p.likes DESC",
            "Most Commented": "p.comments DESC"
        }.get(sort_by, "p.post_date DESC")
        
        # Get total count (for pagination)
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
        posts = []
        for r in rows:
            posts.append({
                "id": r[0],
                "text": r[1],
                "post_date": r[2],
                "likes": r[3],
                "comments": r[4],
                "shares": r[5],
                "total_engagements": r[6],
                "engagement_rate": r[7],
                "svg_image": r[8],
                "category": r[9],
                "tags": r[10],
                "location": r[11],
                "author": {
                    "first_name": r[12],
                    "last_name": r[13],
                    "email": r[14],
                    "company": r[15],
                    "job_title": r[16],
                    "bio": r[17],
                    "follower_count": r[18],
                    "verified": bool(r[19])
                }
            })
        
        logging.debug(f"Retrieved {len(posts)} posts (page {page}/{total_pages}, total: {total})")
        
        return {
            "posts": posts,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    except Exception as e:
        logging.error(f"Error fetching posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/posts/stats")
def get_posts_stats():
    """Get statistics for all posts (for header) - direct SQLite query"""
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Get total posts, total likes, total comments, average engagement rate
        c.execute("""
            SELECT 
                COUNT(*) as total_posts,
                SUM(likes) as total_likes,
                SUM(comments) as total_comments,
                AVG(engagement_rate) as avg_engagement_rate
            FROM posts
        """)
        row = c.fetchone()
        
        return {
            "total_posts": row[0] or 0,
            "total_likes": row[1] or 0,
            "total_comments": row[2] or 0,
            "avg_engagement_rate": round(float(row[3] or 0), 1)
        }
    except Exception as e:
        logging.error(f"Error fetching stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/posts")
def create_post(post_data: PostCreate):
    """Create a new post - direct SQLite insert"""
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Check if author exists by email, if not create one
        c.execute("SELECT id FROM authors WHERE email = ?", (post_data.email,))
        author_row = c.fetchone()
        
        if author_row:
            author_id = author_row[0]
            # Update author info if provided
            update_fields = []
            update_values = []
            
            if post_data.first_name:
                update_fields.append("first_name = ?")
                update_values.append(post_data.first_name)
            if post_data.last_name:
                update_fields.append("last_name = ?")
                update_values.append(post_data.last_name)
            if post_data.company:
                update_fields.append("company = ?")
                update_values.append(post_data.company)
            if post_data.job_title:
                update_fields.append("job_title = ?")
                update_values.append(post_data.job_title)
            
            if update_fields:
                update_values.append(author_id)
                c.execute(f"""
                    UPDATE authors 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """, update_values)
        else:
            # Create new author
            c.execute("""
                INSERT INTO authors (first_name, last_name, email, company, job_title, bio, follower_count, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post_data.first_name,
                post_data.last_name,
                post_data.email,
                post_data.company,
                post_data.job_title,
                "",
                0,
                True
            ))
            author_id = c.lastrowid
        
        # Get the next post ID
        c.execute("SELECT MAX(id) FROM posts")
        max_id_result = c.fetchone()
        next_id = (max_id_result[0] or 0) + 1
        
        # Get current date/time
        post_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the post directly to database
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
        logging.info(f"Post created with ID: {next_id}")
        
        return {
            "id": next_id,
            "message": "Post created successfully"
        }
    except sqlite3.IntegrityError as e:
        logging.error(f"Database integrity error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except Exception as e:
        logging.error(f"Error creating post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/posts/{post_id}")
def update_post(post_id: int, post_data: PostUpdate):
    """Update an existing post - direct SQLite update"""
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Check if post exists
        c.execute("SELECT id, author_id FROM posts WHERE id = ?", (post_id,))
        post_row = c.fetchone()
        
        if not post_row:
            raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found")
        
        author_id = post_row[1]
        
        # Update author if author fields are provided
        # In Pydantic: None = field not provided, empty string = field provided but empty
        author_update_fields = []
        author_update_values = []
        
        if post_data.first_name is not None:
            author_update_fields.append("first_name = ?")
            author_update_values.append(post_data.first_name)
        if post_data.last_name is not None:
            author_update_fields.append("last_name = ?")
            author_update_values.append(post_data.last_name)
        if post_data.email is not None:
            # Check if email is already used by another author (only if email is being changed)
            c.execute("SELECT email FROM authors WHERE id = ?", (author_id,))
            current_email = c.fetchone()
            if current_email and current_email[0] != post_data.email:
                c.execute("SELECT id FROM authors WHERE email = ? AND id != ?", (post_data.email, author_id))
                if c.fetchone():
                    raise HTTPException(status_code=400, detail="Email already exists for another author")
            author_update_fields.append("email = ?")
            author_update_values.append(post_data.email)
        if post_data.company is not None:
            # Empty string means clear the field (set to NULL)
            author_update_fields.append("company = ?")
            author_update_values.append(post_data.company if post_data.company else None)
        if post_data.job_title is not None:
            # Empty string means clear the field (set to NULL)
            author_update_fields.append("job_title = ?")
            author_update_values.append(post_data.job_title if post_data.job_title else None)
        
        if author_update_fields:
            author_update_values.append(author_id)
            c.execute(f"""
                UPDATE authors 
                SET {', '.join(author_update_fields)}
                WHERE id = ?
            """, author_update_values)
        
        # Update post fields
        post_update_fields = []
        post_update_values = []
        
        if post_data.text is not None:
            post_update_fields.append("text = ?")
            post_update_values.append(post_data.text)
        if post_data.category is not None:
            # Empty string means clear the field (set to NULL)
            post_update_fields.append("category = ?")
            post_update_values.append(post_data.category if post_data.category else None)
        if post_data.svg_image is not None:
            # Empty string means clear the field (set to NULL)
            post_update_fields.append("svg_image = ?")
            post_update_values.append(post_data.svg_image if post_data.svg_image else None)
        if post_data.tags is not None:
            # Empty string means clear the field (set to NULL)
            post_update_fields.append("tags = ?")
            post_update_values.append(post_data.tags if post_data.tags else None)
        if post_data.location is not None:
            # Empty string means clear the field (set to NULL)
            post_update_fields.append("location = ?")
            post_update_values.append(post_data.location if post_data.location else None)
        
        if post_update_fields:
            post_update_values.append(post_id)
            c.execute(f"""
                UPDATE posts 
                SET {', '.join(post_update_fields)}
                WHERE id = ?
            """, post_update_values)
        
        conn.commit()
        logging.info(f"Post {post_id} updated successfully")
        
        return {
            "message": "Post updated successfully",
            "id": post_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/posts/{post_id}")
def delete_post(post_id: int):
    """Delete a post - direct SQLite delete"""
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        c = conn.cursor()
        
        # Check if post exists
        c.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
        post = c.fetchone()
        
        if not post:
            raise HTTPException(status_code=404, detail=f"Post with ID {post_id} not found")
        
        # Delete the post directly from database
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        
        logging.info(f"Post {post_id} deleted successfully")
        
        return {
            "message": "Post deleted successfully",
            "id": post_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
