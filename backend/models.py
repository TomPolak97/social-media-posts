from pydantic import BaseModel
from typing import Optional

class Author(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    company: Optional[str]
    job_title: Optional[str]
    bio: Optional[str]
    follower_count: int
    verified: bool

class Post(BaseModel):
    id: int
    author_id: int
    text: str
    post_date: str
    likes: int
    comments: int
    shares: int
    total_engagements: int
    engagement_rate: float
    svg_image: Optional[str]
    category: Optional[str]
    tags: Optional[str]
    location: Optional[str]
