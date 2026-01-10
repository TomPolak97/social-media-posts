import sqlite3
import pandas as pd

# Connect to your database
conn = sqlite3.connect("social_media_posts.db")

# List tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables:", tables)

# Preview authors
authors = pd.read_sql_query("SELECT * FROM authors LIMIT 5;", conn)
print(authors)

# Preview posts
posts = pd.read_sql_query("SELECT * FROM posts LIMIT 5;", conn)
print(posts)

conn.close()
