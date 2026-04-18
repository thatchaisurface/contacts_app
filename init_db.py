"""Run this once to initialize the database."""
import sqlite3
from datetime import datetime

DB = 'contacts.db'

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    relationship TEXT,
    birthday TEXT,
    last_contacted TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
)
""")

conn.commit()
conn.close()
print(f"Database '{DB}' initialized.")