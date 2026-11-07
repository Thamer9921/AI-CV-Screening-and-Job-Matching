import hashlib
import hmac
import re
import secrets
import sqlite3

from database.db import get_connection, init_db


def normalize_email(email):
    return email.strip().lower()


def is_valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


def init_auth_db():
    init_db()


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=16384,
        r=8,
        p=1,
        dklen=32,
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):
    try:
        method, salt_hex, digest_hex = stored_hash.split("$")
        if method != "scrypt":
            return False

        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        if len(salt) != 16 or len(expected) != 32:
            return False

        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=16384,
            r=8,
            p=1,
            dklen=32,
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False


def register_user(full_name, email, password):
    name = full_name.strip()
    email = normalize_email(email)

    if not name or len(name) > 120:
        return False, "Enter a name between 1 and 120 characters."
    if not is_valid_email(email) or len(email) > 254:
        return False, "Enter a valid email address."
    if not 8 <= len(password) <= 256:
        return False, "Password must contain 8 to 256 characters."

    password_hash = hash_password(password)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (email, full_name, password_hash)
                VALUES (?, ?, ?)
                """,
                (email, name, password_hash),
            )
            conn.execute(
                "INSERT INTO user_profiles (email) VALUES (?)",
                (email,),
            )
        return True, None
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."


def login_user(email, password):
    if not 8 <= len(password) <= 256:
        return False, "Incorrect email or password."

    with get_connection() as conn:
        row = conn.execute(
            "SELECT full_name, password_hash FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        return False, "Incorrect email or password."

    return True, row["full_name"]


def load_user_profile(email):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.full_name, p.preferred_location, p.job_type,
                   p.field_of_interest, p.github_username
            FROM users AS u
            JOIN user_profiles AS p ON p.email = u.email
            WHERE u.email = ?
            """,
            (normalize_email(email),),
        ).fetchone()

    if row is None:
        raise ValueError("User profile not found.")

    return dict(row)


def save_user_profile(
    email,
    full_name,
    preferred_location,
    job_type,
    field_of_interest,
    github_username=None,
):
    email = normalize_email(email)
    name = full_name.strip()

    if not name or len(name) > 120:
        raise ValueError("Enter a name between 1 and 120 characters.")

    github = None
    if github_username is not None:
        github = github_username.strip()
        if github and not re.fullmatch(
            r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?",
            github,
        ):
            raise ValueError("Enter a GitHub username, not a URL.")

    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM user_profiles WHERE email = ?",
            (email,),
        ).fetchone()
        if exists is None:
            raise ValueError("User profile not found.")

        conn.execute(
            "UPDATE users SET full_name = ? WHERE email = ?",
            (name, email),
        )
        conn.execute(
            """
            UPDATE user_profiles
            SET preferred_location = ?,
                job_type = ?,
                field_of_interest = ?,
                github_username = COALESCE(?, github_username),
                updated_at = CURRENT_TIMESTAMP
            WHERE email = ?
            """,
            (
                preferred_location.strip(),
                job_type.strip(),
                field_of_interest.strip(),
                github,
                email,
            ),
        )


def save_user_cv(email, cv_filename, cv_bytes):
    from agents.cv_agent import extract_text

    # Validate readability and size before replacing a saved CV.
    extract_text(cv_filename, cv_bytes)
    filename = cv_filename.replace("\\", "/").rsplit("/", 1)[-1]

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_cvs (email, cv_filename, cv_bytes)
            VALUES (?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                cv_filename = excluded.cv_filename,
                cv_bytes = excluded.cv_bytes,
                uploaded_at = CURRENT_TIMESTAMP
            """,
            (normalize_email(email), filename, cv_bytes),
        )


def load_user_cv(email):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cv_filename, cv_bytes FROM user_cvs WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()

    if row is None:
        return None, None

    return row["cv_filename"], bytes(row["cv_bytes"])


def delete_user_cv(email):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM user_cvs WHERE email = ?",
            (normalize_email(email),),
        )