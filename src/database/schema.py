import sqlite3
import os

DB_PATH = "reviews_pulse.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table for tracking runs (idempotency)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT NOT NULL,
        iso_week TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        doc_section_id TEXT,
        gmail_message_id TEXT,
        metrics_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(product_id, iso_week)
    )
    ''')

    # Table for raw reviews
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews_raw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        source TEXT NOT NULL, -- 'app_store' or 'google_play'
        review_id TEXT,
        user_name TEXT,
        rating INTEGER,
        content TEXT NOT NULL,
        review_date TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES runs (id)
    )
    ''')

    # Table for delivery metadata
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        platform TEXT NOT NULL, -- 'google_docs' or 'gmail'
        identifier TEXT, -- section link or message id
        delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (run_id) REFERENCES runs (id)
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
