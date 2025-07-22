from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import ConversationHandler, MessageHandler, ContextTypes, filters

from utils import get_book_by_qr, save_book, get_user_books, log_action, is_admin
from .start import USER_KEYBOARD, ADMIN_KEYBOARD

TAKE_QR, RETURN_QR = range(2)


async def take_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отправьте QR-код книги:")
    return TAKE_QR


async def take_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    qr = update.message.text.strip()
    book = get_book_by_qr(qr)
    if not book:
        await update.message.reply_text("⚠️ Книга с таким QR не найдена.")
    elif book.get("status") == "taken":
        await update.message.reply_text("⚠️ Эта книга уже взята другим пользователем.")
    else:
        book["status"] = "taken"
        book["taken_by"] = update.effective_user.id
        book["taken_date"] = datetime.now().strftime("%Y-%m-%d")
        save_book(book)
        await update.message.reply_text(
            f'✅ Книга "{book.get("title")}" успешно закреплена за вами.'
        )
        log_action(
            "take_book", {"user_id": update.effective_user.id, "qr_code": qr}
        )
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id) else USER_KEYBOARD
    await update.message.reply_text("Главное меню", reply_markup=keyboard)
    return ConversationHandler.END


async def return_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отправьте QR-код книги для возврата:")
    return RETURN_QR


async def return_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    qr = update.message.text.strip()
    book = get_book_by_qr(qr)
    if not book or book.get("taken_by") != update.effective_user.id:
        await update.message.reply_text("⚠️ Эта книга не закреплена за вами.")
    else:
        book["status"] = "available"
        book["taken_by"] = None
        book["taken_date"] = None
        save_book(book)
        await update.message.reply_text(
            f'✅ Книга "{book.get("title")}" возвращена.'
        )
        log_action(
            "return_book", {"user_id": update.effective_user.id, "qr_code": qr}
        )
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id) else USER_KEYBOARD
    await update.message.reply_text("Главное меню", reply_markup=keyboard)
    return ConversationHandler.END


async def my_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    books = get_user_books(update.effective_user.id)
    if not books:
        await update.message.reply_text("У вас нет взятых книг.")
        return
    lines = [
        f'{b.get("title")}, взята {b.get("taken_date")}'
        for b in books
    ]
    await update.message.reply_text("\n".join(lines))


def get_handlers() -> list:
    return [
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🔍 Взять книгу$"), take_book_start)],
            states={TAKE_QR: [MessageHandler(filters.TEXT & ~filters.COMMAND, take_book_get_qr)]},
            fallbacks=[],
        ),
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📤 Вернуть книгу$"), return_book_start)],
            states={RETURN_QR: [MessageHandler(filters.TEXT & ~filters.COMMAND, return_book_get_qr)]},
            fallbacks=[],
        ),
        MessageHandler(filters.Regex("^📚 Мои книги$"), my_books),
    ]

