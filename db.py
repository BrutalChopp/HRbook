import os
from contextlib import contextmanager

from dotenv import load_dotenv
import psycopg2

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
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])


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
