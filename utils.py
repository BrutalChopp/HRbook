from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

import config
import db

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


def _normalize(text: str) -> str:
    """Return a normalized string for office comparison."""
    return text.strip().lower().replace("ё", "е")


def resolve_office_name(name: str) -> Optional[str]:
    """Return canonical office key matching the provided text."""
    offices = getattr(config, "OFFICES", {})
    name_clean = _normalize(name)
    for key, info in offices.items():
        if _normalize(key) == name_clean:
            return key
        if _normalize(str(info.get("name", ""))) == name_clean:
            return key
        for alias in info.get("aliases", []):
            if _normalize(str(alias)) == name_clean:
                return key
    return None


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Return user data for the given Telegram ID."""
    return await db.get_user(user_id)


async def register_user(
    user_id: int, first_name: str, last_name: str, office: str
) -> Dict[str, Any]:
    """Register a user or update their Telegram ID."""
    existing = await db.get_user_by_name(first_name, last_name, office)
    if existing:
        existing["telegram_id"] = user_id
        await db.save_user(existing)
        log_action("login_user", existing)
        return existing

    user = {
        "telegram_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "office": office,
        "role": "admin" if is_admin(user_id, office) else "user",
    }
    await db.save_user(user)
    log_action("register_user", user)
    return user


async def update_user_office(user_id: int, office: str) -> Optional[Dict[str, Any]]:
    """Update the office for an existing user."""
    user = await db.get_user(user_id)
    if not user:
        return None
    role = "admin" if is_admin(user_id, office) else "user"
    await db.update_user_office(user_id, office, role)
    user.update({"office": office, "role": role})
    log_action("update_office", {"user_id": user_id, "office": office})
    return user


async def get_book_by_qr(qr: str) -> Optional[Dict[str, Any]]:
    return await db.get_book_by_qr(qr)


async def get_user_books(user_id: int) -> List[Dict[str, Any]]:
    return await db.get_user_books(user_id)


async def get_books_by_office(office: str) -> List[Dict[str, Any]]:
    """Return all books stored in the given office."""
    return await db.get_books_by_office(office)


async def save_book(book: Dict[str, Any]) -> None:
    await db.save_book(book)


async def get_all_users() -> List[Dict[str, Any]]:
    return await db.get_all_users()


async def delete_user(user_id: int) -> None:
    await db.delete_user(user_id)


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

