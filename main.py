from __future__ import annotations

import logging
import os
import sys
import atexit

from telegram.ext import Application

import config
from handlers.start import (
    get_handler as start_handler,
    get_menu_handler,
    get_change_office_handler,
)
from handlers.books import get_handlers as books_handlers
from handlers.admin import get_handlers as admin_handlers
from handlers.logging import get_handlers as logging_handlers
import db

LOCK_FILE = "/tmp/hrbook_bot.lock"


def acquire_lock() -> None:
    """Create a lock file to ensure a single running instance."""
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w") as f:
            f.write(str(os.getpid()))
    except FileExistsError:
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                pid = f.read().strip()
        except OSError:
            pid = "unknown"
        logging.error("Another bot instance is already running (PID %s).", pid)
        sys.exit(1)


def release_lock() -> None:
    """Remove the lock file on shutdown."""
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    acquire_lock()
    atexit.register(release_lock)
    application = Application.builder().token(config.BOT_TOKEN).build()

    import asyncio
    try:
        asyncio.run(db.init_db())
    except Exception as exc:
        logging.error("Database unavailable: %s", exc)
    asyncio.set_event_loop(asyncio.new_event_loop())

    application.add_handler(start_handler())
    application.add_handler(get_menu_handler())
    application.add_handler(get_change_office_handler())
    for handler in books_handlers():
        application.add_handler(handler)
    for handler in admin_handlers():
        application.add_handler(handler)
    for handler in logging_handlers():
        application.add_handler(handler, group=100)

    logging.info("Bot started")
    application.run_polling()


if __name__ == "__main__":
    main()
