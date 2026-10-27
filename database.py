import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "health_records.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                email TEXT NOT NULL,
                glucose REAL NOT NULL,
                haemoglobin REAL NOT NULL,
                cholesterol REAL NOT NULL,
                remarks TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS import_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_no TEXT NOT NULL,
                full_name TEXT NOT NULL,
                raw_date_of_birth TEXT NOT NULL,
                raw_email TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def _now():
    return datetime.now().astimezone().isoformat(timespec="seconds")

def patient_exists(patient):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id FROM patients
            WHERE lower(full_name)=lower(?) AND date_of_birth=? AND lower(email)=lower(?)
            LIMIT 1
        """, (patient["full_name"], patient["date_of_birth"], patient["email"])).fetchone()
        return row is not None

def create_patient(patient, remarks):
    now = _now()
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO patients
            (full_name, date_of_birth, email, glucose, haemoglobin, cholesterol, remarks, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient["full_name"], patient["date_of_birth"], patient["email"],
            patient["glucose"], patient["haemoglobin"], patient["cholesterol"],
            remarks, now, now
        ))
        return cur.lastrowid

def list_patients():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM patients ORDER BY id").fetchall()
        return [dict(row) for row in rows]

def get_patient(patient_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
        return dict(row) if row else None

def update_patient(patient_id, patient, remarks):
    with get_connection() as conn:
        conn.execute("""
            UPDATE patients SET full_name=?, date_of_birth=?, email=?, glucose=?, haemoglobin=?,
                cholesterol=?, remarks=?, updated_at=? WHERE id=?
        """, (
            patient["full_name"], patient["date_of_birth"], patient["email"],
            patient["glucose"], patient["haemoglobin"], patient["cholesterol"],
            remarks, _now(), patient_id
        ))

def delete_patient(patient_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))

def log_import_result(test_no, raw, status, message):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO import_logs (test_no, full_name, raw_date_of_birth, raw_email, status, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(test_no), raw.get("full_name", ""), raw.get("date_of_birth", ""),
            raw.get("email", ""), status, message, _now()
        ))

def list_import_logs():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM import_logs ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]
