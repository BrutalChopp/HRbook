from __future__ import annotations

from telegram import Update
from telegram.ext import ConversationHandler, MessageHandler, ContextTypes, filters

from utils import (
    is_admin,
    save_book,
    get_book_by_qr,
    log_action,
    get_books_by_office,
    get_user,
    extract_qr_from_update,
    get_all_users,
    delete_user,
)
from .start import (
    ADMIN_KEYBOARD,
    CANCEL_KEYBOARD,
    CANCEL_RE,
    cancel_action,
)

ADD_QR, ADD_TITLE, RESET_QR, REMOVE_USER = range(4)


async def add_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    if not is_admin(update.effective_user.id, office):
        await update.message.reply_text("Недостаточно прав.")
        return ConversationHandler.END
    await update.message.reply_text(
        "Отправьте QR-код новой книги:", reply_markup=CANCEL_KEYBOARD
    )
    return ADD_QR


async def add_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    qr = await extract_qr_from_update(update, context.bot)
    if not qr:
        await update.message.reply_text(
            "Не удалось распознать QR-код. Отправьте текстовый код.",
            reply_markup=CANCEL_KEYBOARD,
        )
        return ADD_QR
    if await get_book_by_qr(qr):
        await update.message.reply_text("⚠️ Книга с таким QR уже существует.")
        await update.message.reply_text("Главное меню", reply_markup=ADMIN_KEYBOARD)
        return ConversationHandler.END
    context.user_data["qr"] = qr
    await update.message.reply_text(
        "Введите название книги:", reply_markup=CANCEL_KEYBOARD
    )
    return ADD_TITLE


async def add_book_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    book = {
        "qr_code": context.user_data.get("qr"),
        "title": title,
        "status": "available",
        "taken_by": None,
        "taken_date": None,
        "office": office,
    }
    await save_book(book)
    await update.message.reply_text("✅ Книга добавлена.")
    log_action("add_book", book)
    await update.message.reply_text("Главное меню", reply_markup=ADMIN_KEYBOARD)
    return ConversationHandler.END


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    if not is_admin(update.effective_user.id, office):
        return
    books = await get_books_by_office(office)
    lines = []
    for b in books:
        if b.get("status") == "taken":
            status = f'взята {b.get("taken_date")}, {b.get("taken_by")}'
        else:
            status = "свободна"
        lines.append(f'{b.get("title")}: {status}')
    await update.message.reply_text("\n".join(lines) if lines else "Нет книг")


async def reset_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    if not is_admin(update.effective_user.id, office):
        await update.message.reply_text("Недостаточно прав.")
        return ConversationHandler.END
    await update.message.reply_text(
        "QR-код книги для сброса:", reply_markup=CANCEL_KEYBOARD
    )
    return RESET_QR


async def reset_book_get_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    qr = update.message.text.strip()
    book = await get_book_by_qr(qr)
    if not book:
        await update.message.reply_text("⚠️ Книга не найдена.")
    elif book.get("office") != office:
        await update.message.reply_text("⚠️ Эта книга находится в другом офисе.")
    else:
        book["status"] = "available"
        book["taken_by"] = None
        book["taken_date"] = None
        await save_book(book)
        await update.message.reply_text("✅ Статус книги сброшен.")
        log_action("reset_book", {"qr_code": qr})
    await update.message.reply_text("Главное меню", reply_markup=ADMIN_KEYBOARD)
    return ConversationHandler.END


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    if not is_admin(update.effective_user.id, office):
        return
    users = await get_all_users()
    lines = [
        f'{u.get("last_name")} {u.get("first_name")} - {u.get("office")}'
        for u in users
        if u.get("office") == office
    ]
    await update.message.reply_text("\n".join(lines) if lines else "Нет пользователей")


async def remove_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = await get_user(update.effective_user.id)
    office = user.get("office") if user else None
    if not is_admin(update.effective_user.id, office):
        await update.message.reply_text("Недостаточно прав.")
        return ConversationHandler.END
    await update.message.reply_text(
        "ID пользователя для удаления:", reply_markup=CANCEL_KEYBOARD
    )
    return REMOVE_USER


async def remove_user_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id_text = update.message.text.strip()
    if not user_id_text.isdigit():
        await update.message.reply_text(
            "Введите числовой ID.", reply_markup=CANCEL_KEYBOARD
        )
        return REMOVE_USER
    target_id = int(user_id_text)
    if not await get_user(target_id):
        await update.message.reply_text(
            "Пользователь не найден.", reply_markup=ADMIN_KEYBOARD
        )
        return ConversationHandler.END
    await delete_user(target_id)
    log_action("delete_user", {"user_id": target_id})
    await update.message.reply_text(
        "✅ Пользователь удалён.", reply_markup=ADMIN_KEYBOARD
    )
    return ConversationHandler.END


def get_handlers() -> list:
    return [
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^➕ Добавить книгу$"), add_book_start)],
            states={
                ADD_QR: [
                    MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                    MessageHandler(~filters.COMMAND, add_book_get_qr),
                ],
                ADD_TITLE: [
                    MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_get_title),
                ],
            },
            fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
        ),
        MessageHandler(filters.Regex("^📊 Отчёт по библиотеке$"), report),
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🔁 Сброс книги$"), reset_book_start)],
            states={
                RESET_QR: [
                    MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, reset_book_get_qr),
                ]
            },
            fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
        ),
        MessageHandler(filters.Regex("^👤 Список пользователей$"), list_users),
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🗑 Удалить пользователя$"), remove_user_start)],
            states={
                REMOVE_USER: [
                    MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, remove_user_process),
                ]
            },
            fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
        ),
    ]

