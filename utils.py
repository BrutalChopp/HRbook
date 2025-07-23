from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

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


def is_admin(user_id: int, office: Optional[str] = None) -> bool:
    """Return True if the user is an admin globally or for the given office."""
    admin_ids = [str(a) for a in getattr(config, "ADMIN_IDS", [])]
    if str(user_id) in admin_ids:
        return True
    offices = getattr(config, "OFFICES", {})
    if office:
        office_admins = [str(a) for a in offices.get(office, {}).get("admins", [])]
        return str(user_id) in office_admins
    for info in offices.values():
        if str(user_id) in [str(a) for a in info.get("admins", [])]:
            return True
    return False


def resolve_office_name(name: str) -> Optional[str]:
    """Return canonical office key matching the provided text."""
    offices = getattr(config, "OFFICES", {})
    name_clean = name.strip().lower()
    for key, info in offices.items():
        if key.lower() == name_clean:
            return key
        if str(info.get("name", "")).lower() == name_clean:
            return key
        for alias in info.get("aliases", []):
            if str(alias).lower() == name_clean:
                return key
    return None


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Return user data for the given Telegram ID."""
    users = load_json("users.json")
    for user in users:
        if user.get("telegram_id") == user_id:
            return user
    return None


def register_user(
    user_id: int, first_name: str, last_name: str, office: str
) -> Dict[str, Any]:
    """Register a user or update their Telegram ID."""
    users = load_json("users.json")
    for usr in users:
        if (
            usr.get("first_name") == first_name
            and usr.get("last_name") == last_name
            and usr.get("office") == office
        ):
            usr["telegram_id"] = user_id
            save_json("users.json", users)
            log_action("login_user", usr)
            return usr

    user = {
        "telegram_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "office": office,
        "role": "admin" if is_admin(user_id, office) else "user",
    }
    users.append(user)
    save_json("users.json", users)
    log_action("register_user", user)
    return user


def update_user_office(user_id: int, office: str) -> Optional[Dict[str, Any]]:
    """Update the office for an existing user."""
    users = load_json("users.json")
    for usr in users:
        if usr.get("telegram_id") == user_id:
            usr["office"] = office
            usr["role"] = "admin" if is_admin(user_id, office) else "user"
            save_json("users.json", users)
            log_action("update_office", {"user_id": user_id, "office": office})
            return usr
    return None


def get_book_by_qr(qr: str) -> Optional[Dict[str, Any]]:
    books = load_json("books.json")
    for book in books:
        if book.get("qr_code") == qr:
            return book
    return None


def get_user_books(user_id: int) -> List[Dict[str, Any]]:
    books = load_json("books.json")
    return [b for b in books if b.get("taken_by") == user_id and b.get("status") == "taken"]


def get_books_by_office(office: str) -> List[Dict[str, Any]]:
    """Return all books stored in the given office."""
    books = load_json("books.json")
    return [b for b in books if b.get("office") == office]


def save_book(book: Dict[str, Any]) -> None:
    books = load_json("books.json")
    for i, b in enumerate(books):
        if b.get("qr_code") == book.get("qr_code"):
            books[i] = book
            break
    else:
        books.append(book)
    save_json("books.json", books)


async def extract_qr_from_update(update, bot) -> Optional[str]:
    """Return QR code text from a message if available.

    The function first tries to read text or caption. If none is present, it will
    attempt to decode a QR code from an attached image (photo or document).
    """

    message = update.effective_message
    qr = (message.text or message.caption or "").strip()
    if qr:
        return qr

    file = None
    if message.photo:
        file = await message.photo[-1].get_file()
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        file = await message.document.get_file()

    if not file:
        return None

    data = await file.download_as_bytearray()
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    detector = cv2.QRCodeDetector()
    decoded, _, _ = detector.detectAndDecode(img)
    return decoded.strip() if decoded else None


def log_action(action_type: str, data: Dict[str, Any]) -> None:
    logging.info("%s %s: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action_type, data)

