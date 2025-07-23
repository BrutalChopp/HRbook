from __future__ import annotations

from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

from utils import is_admin, get_user
from .start import ADMIN_KEYBOARD


async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log incoming messages to the application logger."""
    message = update.effective_message
    if message:
        text = message.text or message.caption or ""
        context.application.logger.info(
            "Message from %s: %s", update.effective_user.id, text
        )


async def clear_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete all stored messages (admin only)."""
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    if not is_admin(update.effective_user.id, office):
        await update.message.reply_text("Недостаточно прав.")
        return
    await update.message.reply_text(
        "История сообщений не сохраняется.", reply_markup=ADMIN_KEYBOARD
    )


def get_handlers() -> list:
    return [
        CommandHandler("clear_logs", clear_logs),
        MessageHandler(filters.ALL, log_message, block=False),
    ]
