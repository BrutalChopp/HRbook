from __future__ import annotations

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

import db
from utils import is_admin, get_user
from .start import ADMIN_KEYBOARD


async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store any incoming message text in the database."""
    message = update.effective_message
    if message:
        text = message.text or message.caption or ""
        try:
            db.save_message(update.effective_user.id, text)
        except Exception as exc:
            # Avoid crashing handlers if DB is unavailable
            context.application.logger.error("Failed to log message: %s", exc)


async def clear_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete all stored messages (admin only)."""
    user = get_user(update.effective_user.id)
    office = user.get("office") if user else None
    if not is_admin(update.effective_user.id, office):
        await update.message.reply_text("Недостаточно прав.")
        return
    db.delete_all_messages()
    await update.message.reply_text("Логи удалены.", reply_markup=ADMIN_KEYBOARD)


def get_handlers() -> list:
    return [
        CommandHandler("clear_logs", clear_logs),
        MessageHandler(filters.ALL, log_message, block=False),
    ]
