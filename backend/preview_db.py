import sqlite3
import pandas as pd

# Connect to your database
conn = sqlite3.connect("social_media_posts.db")

# List tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables:", tables)

# Count posts in database
post_count = conn.execute("SELECT COUNT(*) FROM posts;").fetchone()[0]
print(f"\nTotal Posts in Database: {post_count}")

# Count authors in database
author_count = conn.execute("SELECT COUNT(*) FROM authors;").fetchone()[0]
print(f"Total Authors in Database: {author_count}\n")

# Preview authors
authors = pd.read_sql_query("SELECT * FROM authors LIMIT 5;", conn)
print("Authors (first 5):")
print(authors)

# Preview posts
posts = pd.read_sql_query("SELECT * FROM posts LIMIT 5;", conn)
print("\nPosts (first 5):")
print(posts)

conn.close()
