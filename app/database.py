import os
import json
import sqlite3
from datetime import datetime


DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "audits.db")
AUDITS_COLUMNS = {
    "business_name": "TEXT",
    "website": "TEXT NOT NULL",
    "industry": "TEXT",
    "location": "TEXT",
    "summary": "TEXT",
    "result_json": "TEXT NOT NULL",
    "created_at": "TEXT NOT NULL",
}


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT,
        website TEXT NOT NULL,
        industry TEXT,
        location TEXT,
        summary TEXT,
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    cur.execute("PRAGMA table_info(audits)")
    existing_columns = {row["name"] for row in cur.fetchall()}

    for column_name, column_type in AUDITS_COLUMNS.items():
        if column_name not in existing_columns:
            cur.execute(f"ALTER TABLE audits ADD COLUMN {column_name} {column_type}")

    conn.commit()
    conn.close()


def save_audit(
    business_name: str,
    website: str,
    industry: str,
    location: str,
    summary: str,
    result: dict
) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO audits (business_name, website, industry, location, summary, result_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        business_name,
        website,
        industry,
        location,
        summary,
        json.dumps(result),
        datetime.utcnow().isoformat()
    ))

    audit_id = cur.lastrowid
    conn.commit()
    conn.close()
    return audit_id


def list_audits(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, business_name, website, industry, location, summary, created_at
    FROM audits
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def get_audit(audit_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM audits WHERE id = ?", (audit_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    record = dict(row)
    record["result_json"] = json.loads(record["result_json"])
    return record
