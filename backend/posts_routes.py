from fastapi import APIRouter, HTTPException
import sqlite3
import logging
from db import DB_NAME, create_connection

router = APIRouter()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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
