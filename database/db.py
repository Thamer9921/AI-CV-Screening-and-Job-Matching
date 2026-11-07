import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "runtime" / "ai_match_v2.db"


@contextmanager
def get_connection(db_path=None):
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=None):
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_profiles (
                email TEXT PRIMARY KEY,
                preferred_location TEXT NOT NULL DEFAULT '',
                job_type TEXT NOT NULL DEFAULT '',
                field_of_interest TEXT NOT NULL DEFAULT '',
                github_username TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users(email)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_cvs (
                email TEXT PRIMARY KEY,
                cv_filename TEXT NOT NULL,
                cv_bytes BLOB NOT NULL,
                uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users(email)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                cv_filename TEXT NOT NULL,
                results_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email) REFERENCES users(email)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_analyses_email_id
                ON analyses(email, id);
        """)


def save_analysis(email, cv_filename, results):
    payload = json.dumps(results, ensure_ascii=False, allow_nan=False)

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses (email, cv_filename, results_json)
            VALUES (?, ?, ?)
            """,
            (email.strip().lower(), cv_filename, payload),
        )
        return cursor.lastrowid


def load_analysis_history(email, limit=20):
    limit = max(1, min(int(limit), 100))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, cv_filename, results_json, created_at
            FROM analyses
            WHERE email = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (email.strip().lower(), limit),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "cv_filename": row["cv_filename"],
            "results": json.loads(row["results_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def delete_analysis_history(email):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM analyses WHERE email = ?",
            (email.strip().lower(),),
        )