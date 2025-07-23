import os
from contextlib import contextmanager

from dotenv import load_dotenv
import psycopg2
import sqlite3

# Load environment variables so database configuration works out of the box.
# We first look for a `.env` file in the project root and load it if present.
# If it doesn't exist we fall back to `.env.example` which ships with sample
# values. This mirrors the logic used in :mod:`config`.
base_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(base_dir, ".env")
example_path = os.path.join(base_dir, ".env.example")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
elif os.path.exists(example_path):
    load_dotenv(example_path)

# Required database connection settings. These environment variables must be
# defined or a ``KeyError`` will be raised on import.
DB_ENGINE = os.getenv("DB_ENGINE", "postgres")
if DB_ENGINE == "sqlite":
    DB_NAME = os.getenv("DB_NAME", os.path.join(base_dir, "hrbook.db"))
    DB_USER = DB_PASSWORD = DB_HOST = None
    DB_PORT = None
else:
    DB_NAME = os.environ["DB_NAME"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DB_HOST = os.environ["DB_HOST"]
    DB_PORT = int(os.environ["DB_PORT"])


@contextmanager
def get_conn():
    """Return a database connection context manager."""
    if DB_ENGINE == "sqlite":
        conn = sqlite3.connect(DB_NAME)
    else:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create required tables if they do not exist."""
    with get_conn() as conn:
        cur = conn.cursor()
        id_column = (
            "INTEGER PRIMARY KEY AUTOINCREMENT"
            if DB_ENGINE == "sqlite"
            else "SERIAL PRIMARY KEY"
        )
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS messages (
                id {id_column},
                user_id BIGINT,
                text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                office TEXT,
                role TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                qr_code TEXT PRIMARY KEY,
                title TEXT,
                status TEXT,
                taken_by BIGINT,
                taken_date TEXT,
                office TEXT
            )
            """
        )
        conn.commit()


def save_message(user_id: int, text: str) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"INSERT INTO messages (user_id, text) VALUES ({placeholder}, {placeholder})",
            (user_id, text),
        )
        conn.commit()


def delete_all_messages() -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM messages")
        conn.commit()


def get_user(telegram_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"SELECT telegram_id, first_name, last_name, office, role FROM users WHERE telegram_id = {placeholder}",
            (telegram_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "telegram_id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "office": row[3],
        "role": row[4],
    }


def get_user_by_name(first_name: str, last_name: str, office: str):
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"SELECT telegram_id, first_name, last_name, office, role FROM users WHERE first_name = {placeholder} AND last_name = {placeholder} AND office = {placeholder}",
            (first_name, last_name, office),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "telegram_id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "office": row[3],
        "role": row[4],
    }


def save_user(user: dict) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"""
            INSERT INTO users (telegram_id, first_name, last_name, office, role)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(telegram_id) DO UPDATE SET
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                office=excluded.office,
                role=excluded.role
            """,
            (
                user.get("telegram_id"),
                user.get("first_name"),
                user.get("last_name"),
                user.get("office"),
                user.get("role"),
            ),
        )
        conn.commit()


def update_user_office(telegram_id: int, office: str, role: str) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"UPDATE users SET office = {placeholder}, role = {placeholder} WHERE telegram_id = {placeholder}",
            (office, role, telegram_id),
        )
        conn.commit()


def get_all_users():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT telegram_id, first_name, last_name, office, role FROM users"
        )
        rows = cur.fetchall()
    return [
        {
            "telegram_id": r[0],
            "first_name": r[1],
            "last_name": r[2],
            "office": r[3],
            "role": r[4],
        }
        for r in rows
    ]


def get_book_by_qr(qr: str):
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE qr_code = {placeholder}",
            (qr,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "qr_code": row[0],
        "title": row[1],
        "status": row[2],
        "taken_by": row[3],
        "taken_date": row[4],
        "office": row[5],
    }


def save_book(book: dict) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"""
            INSERT INTO books (qr_code, title, status, taken_by, taken_date, office)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(qr_code) DO UPDATE SET
                title=excluded.title,
                status=excluded.status,
                taken_by=excluded.taken_by,
                taken_date=excluded.taken_date,
                office=excluded.office
            """,
            (
                book.get("qr_code"),
                book.get("title"),
                book.get("status"),
                book.get("taken_by"),
                book.get("taken_date"),
                book.get("office"),
            ),
        )
        conn.commit()


def get_user_books(user_id: int):
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE taken_by = {placeholder} AND status = 'taken'",
            (user_id,),
        )
        rows = cur.fetchall()
    return [
        {
            "qr_code": r[0],
            "title": r[1],
            "status": r[2],
            "taken_by": r[3],
            "taken_date": r[4],
            "office": r[5],
        }
        for r in rows
    ]


def get_books_by_office(office: str):
    with get_conn() as conn:
        cur = conn.cursor()
        placeholder = "?" if DB_ENGINE == "sqlite" else "%s"
        cur.execute(
            f"SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE office = {placeholder}",
            (office,),
        )
        rows = cur.fetchall()
    return [
        {
            "qr_code": r[0],
            "title": r[1],
            "status": r[2],
            "taken_by": r[3],
            "taken_date": r[4],
            "office": r[5],
        }
        for r in rows
    ]

