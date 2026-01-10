from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import logging
from datetime import datetime
from db import DB_NAME, create_connection

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

@router.get("/posts")
def get_posts():
    try:
        conn = create_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="Database connection failed")

        c = conn.cursor()
        c.execute("""
            SELECT p.id, p.text, p.post_date, p.likes, p.comments, p.shares,
                   p.total_engagements, p.engagement_rate, p.svg_image, p.category,
                   p.tags, p.location,
                   a.first_name, a.last_name, a.email, a.company, a.job_title, a.bio, a.follower_count, a.verified
            FROM posts p
            JOIN authors a ON p.author_id = a.id
            ORDER BY p.post_date DESC
        """)
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
        return posts
    except Exception as e:
        logging.error(f"Error fetching posts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


@router.post("/posts")
def create_post(post_data: PostCreate):
    """Create a new post with author information"""
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
            # Update author info if provided (use CASE or direct value)
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
                True  # New authors are verified by default
            ))
            author_id = c.lastrowid

        # Get the next post ID
        c.execute("SELECT MAX(id) FROM posts")
        max_id_result = c.fetchone()
        next_id = (max_id_result[0] or 0) + 1

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
        logging.info(f"Post created successfully with ID: {next_id}")

        return {
            "id": next_id,
            "message": "Post created successfully",
            "author_id": author_id
        }

    except sqlite3.IntegrityError as e:
        logging.error(f"Database integrity error: {e}")
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except Exception as e:
        logging.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


@router.delete("/posts/{post_id}")
def delete_post(post_id: int):
    """Delete a post by ID"""
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

        # Delete the post
        c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()

        logging.info(f"Post deleted successfully with ID: {post_id}")

        return {
            "message": "Post deleted successfully",
            "id": post_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting post: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
