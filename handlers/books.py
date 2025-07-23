from __future__ import annotations

from datetime import datetime

from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from utils import (
    get_book_by_qr,
    save_book,
    get_user_books,
    log_action,
    is_admin,
    get_user,
    get_books_by_office,
    extract_qr_from_update,
)
from .start import (
    USER_KEYBOARD,
    ADMIN_KEYBOARD,
    CANCEL_KEYBOARD,
    CANCEL_RE,
    cancel_action,
)

TAKE_QR, RETURN_QR = range(2)


async def take_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Отправьте QR-код книги:", reply_markup=CANCEL_KEYBOARD
    )
    return TAKE_QR


async def take_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = get_user(update.effective_user.id)
    office = user.get("office") if user else None
    qr = await extract_qr_from_update(update, context.bot)
    if not qr:
        await update.message.reply_text(
            "Не удалось распознать QR-код. Отправьте текстовый код.",
            reply_markup=CANCEL_KEYBOARD,
        )
        return TAKE_QR
    book = get_book_by_qr(qr)
    if not book:
        await update.message.reply_text("⚠️ Книга с таким QR не найдена.")
    elif book.get("office") != office:
        await update.message.reply_text("⚠️ Эта книга находится в другом офисе.")
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
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id, office) else USER_KEYBOARD
    await update.message.reply_text("Главное меню", reply_markup=keyboard)
    return ConversationHandler.END


async def return_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Отправьте QR-код книги для возврата:", reply_markup=CANCEL_KEYBOARD
    )
    return RETURN_QR


async def return_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = get_user(update.effective_user.id)
    office = user.get("office") if user else None
    qr = await extract_qr_from_update(update, context.bot)
    if not qr:
        await update.message.reply_text(
            "Не удалось распознать QR-код. Отправьте текстовый код.",
            reply_markup=CANCEL_KEYBOARD,
        )
        return RETURN_QR
    book = get_book_by_qr(qr)
    if not book or book.get("taken_by") != update.effective_user.id or book.get("office") != office:
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
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id, office) else USER_KEYBOARD
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


async def list_all_books(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_user(update.effective_user.id)
    office = user.get("office") if user else None
    books = get_books_by_office(office)
    if not books:
        await update.message.reply_text("Нет книг")
        return
    lines = []
    for b in books:
        if b.get("status") == "taken":
            user = get_user(b.get("taken_by"))
            if user:
                account = f'{user.get("first_name", "")} {user.get("last_name", "")}'
            else:
                account = str(b.get("taken_by"))
            status = f'взята {b.get("taken_date")}, {account.strip()}'
        else:
            status = "свободна"
        lines.append(f'{b.get("title")}: {status}')
    await update.message.reply_text("\n".join(lines))


def get_handlers() -> list:
    return [
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🔍 Взять книгу$"), take_book_start)],
            states={
                TAKE_QR: [
                    MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                    MessageHandler(~filters.COMMAND, take_book_get_qr),
                ]
            },
            fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
        ),
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📤 Вернуть книгу$"), return_book_start)],
            states={
                RETURN_QR: [
                    MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                    MessageHandler(~filters.COMMAND, return_book_get_qr),
                ]
            },
            fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
        ),
        MessageHandler(filters.Regex("^📚 Мои книги$"), my_books),
        MessageHandler(filters.Regex("^📖 Все книги$"), list_all_books),
    ]

