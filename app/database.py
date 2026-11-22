import os
import sqlite3
from pathlib import Path


class Database:
    def __init__(self, url=None):
        self.url = url or os.getenv("DATABASE_URL")
        self.is_postgres = bool(self.url and self.url.startswith(("postgres://", "postgresql://")))

    def connect(self):
        if self.is_postgres:
            import psycopg2
            import psycopg2.extras
            connection = psycopg2.connect(self.url, cursor_factory=psycopg2.extras.RealDictCursor)
            connection.autocommit = False
            return connection

        instance_dir = Path(os.getenv("INSTANCE_DIR", "instance"))
        if not instance_dir.is_absolute():
            instance_dir = Path(__file__).resolve().parent.parent / instance_dir
        instance_dir.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(instance_dir / "smart_factory.db")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def placeholder(self):
        return "%s" if self.is_postgres else "?"

    def dict_rows(self, cursor):
        if self.is_postgres:
            return cursor.fetchall()
        return [dict(row) for row in cursor.fetchall()]


def migrate_sqlite_employee_fields(connection):
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(employees)").fetchall()
    }
    employee_fields = {
        "nationality": "TEXT",
        "state": "TEXT",
        "district": "TEXT",
        "caste": "TEXT",
        "religion": "TEXT",
        "blood_group": "TEXT",
        "date_of_birth": "TEXT",
        "aadhaar_number": "TEXT",
        "pan_number": "TEXT",
        "voter_id_number": "TEXT",
        "ration_card_number": "TEXT",
        "id_card_type": "TEXT",
        "id_card_number": "TEXT",
        "permanent_address": "TEXT",
        "emergency_contact_name": "TEXT",
    }
    for name, type_name in employee_fields.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE employees ADD COLUMN {name} {type_name}")

    attendance_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(attendance)").fetchall()
    }
    attendance_fields = {
        "total_working_minutes": "INTEGER DEFAULT 0",
        "break_minutes": "INTEGER DEFAULT 30",
        "standard_minutes": "INTEGER DEFAULT 480",
    }
    for name, type_name in attendance_fields.items():
        if name not in attendance_columns:
            connection.execute(f"ALTER TABLE attendance ADD COLUMN {name} {type_name}")


def migrate_sqlite_voice_fields(connection):
    voice_table = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='voice_recordings'"
    ).fetchone()
    if not voice_table:
        return
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(voice_recordings)").fetchall()
    }
    if "retention_until" not in columns:
        connection.execute("ALTER TABLE voice_recordings ADD COLUMN retention_until TEXT")


def init_schema(db):
    connection = db.connect()
    try:
        if db.is_postgres:
            schema_dir = Path(__file__).resolve().parent.parent / "database"
            cursor = connection.cursor()
            cursor.execute((schema_dir / "schema.sql").read_text(encoding="utf-8"))
            cursor.execute((schema_dir / "schema_extended.sql").read_text(encoding="utf-8"))
        else:
            schema_dir = Path(__file__).resolve().parent.parent / "database"
            connection.executescript((schema_dir / "schema.sqlite.sql").read_text(encoding="utf-8"))
            connection.executescript((schema_dir / "schema_extended.sqlite.sql").read_text(encoding="utf-8"))
            migrate_sqlite_employee_fields(connection)
            migrate_sqlite_voice_fields(connection)
        connection.commit()
    finally:
        connection.close()
