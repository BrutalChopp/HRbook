from __future__ import annotations

from telegram import Update
from telegram.ext import ConversationHandler, MessageHandler, ContextTypes, filters

from utils import (
    is_admin,
    load_json,
    save_book,
    get_book_by_qr,
    log_action,
)
from .start import ADMIN_KEYBOARD

ADD_QR, ADD_TITLE, RESET_QR = range(3)


async def add_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Недостаточно прав.")
        return ConversationHandler.END
    await update.message.reply_text("Отправьте QR-код новой книги:")
    return ADD_QR


async def add_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    qr = update.message.text.strip()
    if get_book_by_qr(qr):
        await update.message.reply_text("⚠️ Книга с таким QR уже существует.")
        return ConversationHandler.END
    context.user_data["qr"] = qr
    await update.message.reply_text("Введите название книги:")
    return ADD_TITLE


async def add_book_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    book = {
        "qr_code": context.user_data.get("qr"),
        "title": title,
        "status": "available",
        "taken_by": None,
        "taken_date": None,
    }
    save_book(book)
    await update.message.reply_text("✅ Книга добавлена.")
    log_action("add_book", book)
    await update.message.reply_text("Главное меню", reply_markup=ADMIN_KEYBOARD)
    return ConversationHandler.END


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    books = load_json("books.json")
    lines = []
    for b in books:
        if b.get("status") == "taken":
            status = f'взята {b.get("taken_date")}, {b.get("taken_by")}'
        else:
            status = "свободна"
        lines.append(f'{b.get("title")}: {status}')
    await update.message.reply_text("\n".join(lines) if lines else "Нет книг")


async def reset_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Недостаточно прав.")
        return ConversationHandler.END
    await update.message.reply_text("QR-код книги для сброса:")
    return RESET_QR


async def reset_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    qr = update.message.text.strip()
    book = get_book_by_qr(qr)
    if not book:
        await update.message.reply_text("⚠️ Книга не найдена.")
    else:
        book["status"] = "available"
        book["taken_by"] = None
        book["taken_date"] = None
        save_book(book)
        await update.message.reply_text("✅ Статус книги сброшен.")
        log_action("reset_book", {"qr_code": qr})
    await update.message.reply_text("Главное меню", reply_markup=ADMIN_KEYBOARD)
    return ConversationHandler.END


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        return
    users = load_json("users.json")
    lines = [
        f'{u.get("last_name")} {u.get("first_name")} - {u.get("organization")}'
        for u in users
    ]
    await update.message.reply_text("\n".join(lines) if lines else "Нет пользователей")


def get_handlers() -> list:
    return [
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^➕ Добавить книгу$"), add_book_start)],
            states={
                ADD_QR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_get_qr)],
                ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_get_title)],
            },
            fallbacks=[],
        ),
        MessageHandler(filters.Regex("^📊 Отчёт по библиотеке$"), report),
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🔁 Сброс книги$"), reset_book_start)],
            states={RESET_QR: [MessageHandler(filters.TEXT & ~filters.COMMAND, reset_book_get_qr)]},
            fallbacks=[],
        ),
        MessageHandler(filters.Regex("^👤 Список пользователей$"), list_users),
    ]

