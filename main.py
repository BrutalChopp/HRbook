from __future__ import annotations

import logging

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


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    application = Application.builder().token(config.BOT_TOKEN).build()

    db.init_db()

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
