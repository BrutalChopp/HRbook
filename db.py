import os
import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
import aiosqlite
import asyncpg

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


@asynccontextmanager
async def get_conn():
    """Return an asynchronous database connection context manager."""
    logging.info("Opening %s database connection", DB_ENGINE)
    conn = None
    try:
        if DB_ENGINE == "sqlite":
            conn = await aiosqlite.connect(DB_NAME)
        else:
            conn = await asyncpg.connect(
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
        logging.info("Database connection established")
        yield conn
    except Exception as exc:
        logging.error("Database connection error: %s", exc)
        raise
    finally:
        if conn:
            await conn.close()
            logging.info("Database connection closed")


async def init_db() -> None:
    """Create required tables if they do not exist."""
    async with get_conn() as conn:
        cur = conn
        id_column = (
            "INTEGER PRIMARY KEY AUTOINCREMENT"
            if DB_ENGINE == "sqlite"
            else "SERIAL PRIMARY KEY"
        )
        await cur.execute(
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
        await cur.execute(
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
        if DB_ENGINE == "sqlite":
            await conn.commit()




async def get_user(telegram_id: int):
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            cur = await conn.execute(
                "SELECT telegram_id, first_name, last_name, office, role FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cur.fetchone()
        else:
            row = await conn.fetchrow(
                "SELECT telegram_id, first_name, last_name, office, role FROM users WHERE telegram_id = $1",
                telegram_id,
            )
    if not row:
        return None
    return {
        "telegram_id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "office": row[3],
        "role": row[4],
    }


async def get_user_by_name(first_name: str, last_name: str, office: str):
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            cur = await conn.execute(
                "SELECT telegram_id, first_name, last_name, office, role FROM users WHERE first_name = ? AND last_name = ? AND office = ?",
                (first_name, last_name, office),
            )
            row = await cur.fetchone()
        else:
            row = await conn.fetchrow(
                "SELECT telegram_id, first_name, last_name, office, role FROM users WHERE first_name = $1 AND last_name = $2 AND office = $3",
                first_name,
                last_name,
                office,
            )
    if not row:
        return None
    return {
        "telegram_id": row[0],
        "first_name": row[1],
        "last_name": row[2],
        "office": row[3],
        "role": row[4],
    }


async def save_user(user: dict) -> None:
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            await conn.execute(
                """
                INSERT INTO users (telegram_id, first_name, last_name, office, role)
                VALUES (?, ?, ?, ?, ?)
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
            await conn.commit()
        else:
            await conn.execute(
                """
                INSERT INTO users (telegram_id, first_name, last_name, office, role)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    first_name=excluded.first_name,
                    last_name=excluded.last_name,
                    office=excluded.office,
                    role=excluded.role
                """,
                user.get("telegram_id"),
                user.get("first_name"),
                user.get("last_name"),
                user.get("office"),
                user.get("role"),
            )


async def update_user_office(telegram_id: int, office: str, role: str) -> None:
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            await conn.execute(
                "UPDATE users SET office = ?, role = ? WHERE telegram_id = ?",
                (office, role, telegram_id),
            )
            await conn.commit()
        else:
            await conn.execute(
                "UPDATE users SET office = $1, role = $2 WHERE telegram_id = $3",
                office,
                role,
                telegram_id,
            )


async def delete_user(telegram_id: int) -> None:
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            await conn.execute(
                "DELETE FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            await conn.commit()
        else:
            await conn.execute(
                "DELETE FROM users WHERE telegram_id = $1",
                telegram_id,
            )


async def get_all_users():
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            cur = await conn.execute(
                "SELECT telegram_id, first_name, last_name, office, role FROM users"
            )
            rows = await cur.fetchall()
        else:
            rows = await conn.fetch(
                "SELECT telegram_id, first_name, last_name, office, role FROM users"
            )
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


async def get_book_by_qr(qr: str):
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            cur = await conn.execute(
                "SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE qr_code = ?",
                (qr,),
            )
            row = await cur.fetchone()
        else:
            row = await conn.fetchrow(
                "SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE qr_code = $1",
                qr,
            )
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


async def save_book(book: dict) -> None:
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            await conn.execute(
                """
                INSERT INTO books (qr_code, title, status, taken_by, taken_date, office)
                VALUES (?, ?, ?, ?, ?, ?)
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
            await conn.commit()
        else:
            await conn.execute(
                """
                INSERT INTO books (qr_code, title, status, taken_by, taken_date, office)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT(qr_code) DO UPDATE SET
                    title=excluded.title,
                    status=excluded.status,
                    taken_by=excluded.taken_by,
                    taken_date=excluded.taken_date,
                    office=excluded.office
                """,
                book.get("qr_code"),
                book.get("title"),
                book.get("status"),
                book.get("taken_by"),
                book.get("taken_date"),
                book.get("office"),
            )


async def get_user_books(user_id: int):
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            cur = await conn.execute(
                "SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE taken_by = ? AND status = 'taken'",
                (user_id,),
            )
            rows = await cur.fetchall()
        else:
            rows = await conn.fetch(
                "SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE taken_by = $1 AND status = 'taken'",
                user_id,
            )
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


async def get_books_by_office(office: str):
    async with get_conn() as conn:
        if DB_ENGINE == "sqlite":
            cur = await conn.execute(
                "SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE office = ?",
                (office,),
            )
            rows = await cur.fetchall()
        else:
            rows = await conn.fetch(
                "SELECT qr_code, title, status, taken_by, taken_date, office FROM books WHERE office = $1",
                office,
            )
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

