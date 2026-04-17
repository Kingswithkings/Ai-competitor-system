import os
import json
import sqlite3
from datetime import datetime


DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "audits.db")


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
        summary TEXT,
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def save_audit(business_name: str, website: str, industry: str, summary: str, result: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO audits (business_name, website, industry, summary, result_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        business_name,
        website,
        industry,
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
    SELECT id, business_name, website, industry, summary, created_at
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

    cur.execute("""
    SELECT *
    FROM audits
    WHERE id = ?
    """, (audit_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    record = dict(row)
    record["result_json"] = json.loads(record["result_json"])
    return record