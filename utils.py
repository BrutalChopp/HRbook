from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def load_json(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data: Any) -> None:
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_admin(user_id: int) -> bool:
    return user_id in getattr(config, "ADMIN_IDS", [])


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    users = load_json("users.json")
    for user in users:
        if user.get("telegram_id") == user_id:
            return user
    return None


def register_user(user_id: int, first_name: str, last_name: str, organization: str) -> Dict[str, Any]:
    users = load_json("users.json")
    user = {
        "telegram_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "organization": organization,
        "role": "admin" if is_admin(user_id) else "user",
    }
    users.append(user)
    save_json("users.json", users)
    log_action("register_user", user)
    return user


def get_book_by_qr(qr: str) -> Optional[Dict[str, Any]]:
    books = load_json("books.json")
    for book in books:
        if book.get("qr_code") == qr:
            return book
    return None


def get_user_books(user_id: int) -> List[Dict[str, Any]]:
    books = load_json("books.json")
    return [b for b in books if b.get("taken_by") == user_id and b.get("status") == "taken"]


def save_book(book: Dict[str, Any]) -> None:
    books = load_json("books.json")
    for i, b in enumerate(books):
        if b.get("qr_code") == book.get("qr_code"):
            books[i] = book
            break
    else:
        books.append(book)
    save_json("books.json", books)


def log_action(action_type: str, data: Dict[str, Any]) -> None:
    logging.info("%s %s: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action_type, data)

