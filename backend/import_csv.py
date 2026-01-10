import pandas as pd
import os
import sqlite3
import logging
from db import DB_NAME, create_tables, create_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CSV_FILE = "social_media_posts_data.csv"

def import_csv():
    if not os.path.exists(CSV_FILE):
        logging.warning(f"CSV file not found: {CSV_FILE}")
        return

    try:
        # Read CSV
        df = pd.read_csv(CSV_FILE)
        logging.info(f"CSV loaded successfully: {CSV_FILE}")

        # -----------------------------
        # Data cleaning
        # -----------------------------
        numeric_cols = ["author_follower_count", "likes", "comments", "shares", "total_engagements", "engagement_rate"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        text_cols = ["author_first_name","author_last_name","author_email","author_company","author_job_title",
                     "author_bio","post_text","post_image_svg","post_category","post_tags","location"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("")

        if "author_verified" in df.columns:
            df["author_verified"] = df["author_verified"].apply(lambda x: bool(x) if pd.notnull(x) else False)
        else:
            df["author_verified"] = False

        if "post_date" in df.columns:
            df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce").fillna(pd.Timestamp.now()).astype(str)
        else:
            df["post_date"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

        # -----------------------------
        # Insert into SQLite
        # -----------------------------
        conn = create_connection()
        if conn is None:
            logging.error("No connection available. Cannot import CSV.")
            return
        c = conn.cursor()

        # Insert authors
        authors_dict = {}
        for idx, row in df.iterrows():
            email = row["author_email"]
            if email not in authors_dict:
                try:
                    c.execute("""
                    INSERT OR IGNORE INTO authors (first_name, last_name, email, company, job_title, bio, follower_count, verified)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (row["author_first_name"], row["author_last_name"], row["author_email"], row["author_company"],
                          row["author_job_title"], row["author_bio"], int(row["author_follower_count"]), row["author_verified"]))
                    authors_dict[email] = c.lastrowid
                except sqlite3.Error as e:
                    logging.error(f"Failed to insert author {email}: {e}")

        # Map email to author_id
        c.execute("SELECT id, email FROM authors")
        author_map = {email: id for id, email in c.fetchall()}

        # Insert posts
        for idx, row in df.iterrows():
            author_id = author_map.get(row["author_email"])
            try:
                c.execute("""
                INSERT OR REPLACE INTO posts (id, author_id, text, post_date, likes, comments, shares,
                                              total_engagements, engagement_rate, svg_image, category, tags, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (int(row["post_id"]), author_id, row["post_text"], row["post_date"], int(row["likes"]),
                      int(row["comments"]), int(row["shares"]), int(row["total_engagements"]),
                      float(row["engagement_rate"]), row["post_image_svg"], row["post_category"], row["post_tags"], row["location"]))
            except sqlite3.Error as e:
                logging.error(f"Failed to insert post {row['post_id']}: {e}")

        conn.commit()
        logging.info("CSV imported successfully!")
    except Exception as e:
        logging.error(f"Error importing CSV: {e}")
    finally:
        if conn:
            conn.close()
