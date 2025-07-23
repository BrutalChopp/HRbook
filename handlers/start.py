from __future__ import annotations

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, ContextTypes, filters

import config
from utils import (
    get_user,
    register_user,
    is_admin,
    update_user_office,
    resolve_office_name,
)

CANCEL_TEXT = "\u21a9\ufe0f \u041d\u0430\u0437\u0430\u0434"
# Accept minor variations of the back button text so the handler works even if
# users type "Назад" manually or the arrow symbol differs.
# Accept "Назад" typed manually or with the arrow from the button.

CANCEL_RE = r"(?i).*назад.*"

CANCEL_KEYBOARD = ReplyKeyboardMarkup(
    [[CANCEL_TEXT]], resize_keyboard=True, one_time_keyboard=True
)


def get_office_keyboard() -> ReplyKeyboardMarkup:
    """Return a keyboard with available office names."""
    offices = getattr(config, "OFFICES", {})
    keyboard = [[info.get("name", key)] for key, info in offices.items()]
    keyboard.append([CANCEL_TEXT])
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )

LAST_NAME, FIRST_NAME, OFFICE, NEW_OFFICE = range(4)

USER_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🔍 Взять книгу", "📤 Вернуть книгу"],
        ["📚 Мои книги", "🏢 Сменить офис"],
        ["📖 Все книги"],
    ],
    resize_keyboard=True,
)
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🔍 Взять книгу", "📤 Вернуть книгу"],
        ["📚 Мои книги", "📖 Все книги"],
        ["➕ Добавить книгу", "📊 Отчёт по библиотеке"],
        ["🔁 Сброс книги", "👤 Список пользователей"],
        ["🗑 Удалить пользователя", "🏢 Сменить офис"],
    ],
    resize_keyboard=True,
)


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle action cancellation and show the main menu."""
    user = get_user(update.effective_user.id)
    office = user.get("office") if user else None
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id, office) else USER_KEYBOARD
    await update.message.reply_text("Действие отменено.", reply_markup=keyboard)
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user = get_user(user_id)
    welcome = (
        "\U0001F4DA \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0432 QR \u0431\u0438\u0431\u043b\u0438\u043e\u0442\u0435\u043a\u0443!\n"
        "\u0417\u0434\u0435\u0441\u044c \u0432\u044b \u043c\u043e\u0436\u0435\u0442\u0435 \u0431\u0440\u0430\u0442\u044c \u0438 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0430\u0442\u044c \u043a\u043d\u0438\u0433\u0438 \u043f\u043e QR-\u043a\u043e\u0434\u0430\u043c."
    )
    await update.message.reply_text(welcome)
    if user:
        keyboard = ADMIN_KEYBOARD if is_admin(user_id, user.get("office")) else USER_KEYBOARD
        await update.message.reply_text(
            "\u0421 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0438\u0435\u043c!", reply_markup=keyboard
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0432\u0430\u0448\u0443 \u0444\u0430\u043c\u0438\u043b\u0438\u044e:",
        reply_markup=CANCEL_KEYBOARD,
    )
    return LAST_NAME


async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["last_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Введите ваше имя:", reply_markup=CANCEL_KEYBOARD
    )
    return FIRST_NAME


async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["first_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Выберите офис:", reply_markup=get_office_keyboard()
    )
    return OFFICE


async def get_office(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    office_input = update.message.text.strip()
    office = resolve_office_name(office_input)
    if not office:
        await update.message.reply_text(
            "Неверный офис, выберите из списка.", reply_markup=get_office_keyboard()
        )
        return OFFICE

    user = register_user(
        user_id,
        context.user_data.get("first_name", ""),
        context.user_data.get("last_name", ""),
        office,
    )
    keyboard = ADMIN_KEYBOARD if is_admin(user_id, office) else USER_KEYBOARD
    await update.message.reply_text(
        "✅ Регистрация успешна.", reply_markup=keyboard
    )
    return ConversationHandler.END


async def change_office_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Initiate office change for an existing user."""
    if not get_user(update.effective_user.id):
        await update.message.reply_text(
            "Сначала зарегистрируйтесь командой /start.", reply_markup=USER_KEYBOARD
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "Выберите офис:", reply_markup=get_office_keyboard()
    )
    return NEW_OFFICE


async def set_new_office(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    office_input = update.message.text.strip()
    office = resolve_office_name(office_input)
    if not office:
        await update.message.reply_text(
            "Неверный офис, выберите из списка.", reply_markup=get_office_keyboard()
        )
        return NEW_OFFICE

    update_user_office(update.effective_user.id, office)
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id, office) else USER_KEYBOARD
    await update.message.reply_text(
        "✅ Офис обновлён.", reply_markup=keyboard
    )
    return ConversationHandler.END


def get_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LAST_NAME: [
                MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_name),
            ],
            FIRST_NAME: [
                MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_name),
            ],
            OFFICE: [
                MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_office),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
    )


def get_change_office_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🏢 Сменить офис$"), change_office_start)],
        states={
            NEW_OFFICE: [
                MessageHandler(filters.Regex(CANCEL_RE), cancel_action),
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_new_office),
            ]
        },
        fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
    )


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the main menu keyboard based on user role."""
    user = get_user(update.effective_user.id)
    office = user.get("office") if user else None
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id, office) else USER_KEYBOARD
    await update.message.reply_text("Главное меню", reply_markup=keyboard)


def get_menu_handler() -> CommandHandler:
    """Return handler for the /menu command."""
    return CommandHandler("menu", main_menu)

