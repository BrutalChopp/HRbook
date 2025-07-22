import os
from contextlib import contextmanager
import psycopg2

DB_NAME = os.getenv("DB_NAME", "HRbase")
DB_USER = os.getenv("DB_USER", "Sergey")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Qwerty455")
DB_HOST = os.getenv("DB_HOST", "amvera-sergey13683-cnpg-hrbase-rw")
DB_PORT = int(os.getenv("DB_PORT", "5432"))


@contextmanager
def get_conn():
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
    """Create the messages table if it doesn't exist."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()


def save_message(user_id: int, text: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO messages (user_id, text) VALUES (%s, %s)",
                (user_id, text),
            )
            conn.commit()


def delete_all_messages() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM messages")
            conn.commit()
