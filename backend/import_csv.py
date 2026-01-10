import pandas as pd
import os
import sqlite3
import logging
from datetime import datetime
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
        
        # Trim column names to handle whitespace issues
        df.columns = df.columns.str.strip()
        logging.debug(f"Trimmed column names. Columns: {list(df.columns)}")

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
            else:
                # Add missing column with empty string default
                df[col] = ""
                logging.warning(f"Column '{col}' not found in CSV, using empty string default")
        
        # Ensure required numeric columns exist
        if "author_follower_count" not in df.columns:
            df["author_follower_count"] = 0
            logging.warning("Column 'author_follower_count' not found in CSV, using 0 default")
        
        # Ensure required post_id column exists
        if "post_id" not in df.columns:
            # Generate sequential post IDs if missing
            df["post_id"] = range(1, len(df) + 1)
            logging.warning("Column 'post_id' not found in CSV, generating sequential IDs")

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

        # Insert authors using bulk insert (much faster)
        authors_dict = {}
        unique_authors = {}
        
        for idx, row in df.iterrows():
            try:
                email = row["author_email"]
                if not email or pd.isna(email) or email in unique_authors:
                    continue
                
                first_name = row["author_first_name"] if pd.notna(row["author_first_name"]) else ""
                last_name = row["author_last_name"] if pd.notna(row["author_last_name"]) else ""
                company = row["author_company"] if pd.notna(row["author_company"]) else None
                job_title = row["author_job_title"] if pd.notna(row["author_job_title"]) else None
                bio = row["author_bio"] if pd.notna(row["author_bio"]) else ""
                follower_count = int(row["author_follower_count"]) if pd.notna(row["author_follower_count"]) else 0
                verified = bool(row["author_verified"])
                
                unique_authors[email] = (first_name, last_name, email, company, job_title, bio, follower_count, verified)
            except (KeyError, ValueError) as e:
                logging.error(f"Failed to process author in row {idx}: {e}")
                continue
        
        # Bulk insert authors
        if unique_authors:
            author_values = list(unique_authors.values())
            c.executemany("""
                INSERT OR IGNORE INTO authors (first_name, last_name, email, company, job_title, bio, follower_count, verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, author_values)
            conn.commit()
            logging.debug(f"Bulk inserted {len(unique_authors)} unique authors")

        # Map email to author_id
        c.execute("SELECT id, email FROM authors")
        author_map = {email: id for id, email in c.fetchall()}

        # Prepare posts for bulk insert
        post_values = []
        for idx, row in df.iterrows():
            try:
                email = row["author_email"]
                author_id = author_map.get(email)
                
                if not author_id:
                    continue  # Skip silently - author should exist
                
                post_id = int(row["post_id"]) if pd.notna(row["post_id"]) else 0
                if not post_id:
                    continue  # Skip invalid post IDs
                
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
                
                post_values.append((post_id, author_id, post_text, post_date, likes, comments, shares,
                                   total_engagements, engagement_rate, svg_image, category, tags, location))
            except (KeyError, ValueError) as e:
                logging.error(f"Failed to process post in row {idx}: {e}")
                continue

        # Bulk insert posts (much faster than row-by-row)
        if post_values:
            # Insert in batches to avoid memory issues with very large datasets
            batch_size = 1000
            total_inserted = 0
            for i in range(0, len(post_values), batch_size):
                batch = post_values[i:i + batch_size]
                c.executemany("""
                    INSERT OR REPLACE INTO posts (id, author_id, text, post_date, likes, comments, shares,
                                              total_engagements, engagement_rate, svg_image, category, tags, location)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                total_inserted += len(batch)
                if (i // batch_size + 1) % 10 == 0:
                    logging.info(f"Inserted {total_inserted} posts...")
            
            conn.commit()
            logging.info(f"CSV imported successfully! Inserted {total_inserted} posts and {len(unique_authors)} authors")
        else:
            logging.warning("No posts to insert from CSV")
    except Exception as e:
        logging.error(f"Error importing CSV: {e}")
    finally:
        if conn:
            conn.close()
