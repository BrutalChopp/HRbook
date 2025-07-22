from __future__ import annotations

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, ContextTypes, filters

from utils import get_user, register_user, is_admin

CANCEL_TEXT = "\u21a9\ufe0f \u041d\u0430\u0437\u0430\u0434"
# Accept minor variations of the back button text so the handler works even if
# users type "Назад" manually or the arrow symbol differs.
CANCEL_RE = r"(?i)^\u21a9\ufe0f?\s*назад$"
CANCEL_KEYBOARD = ReplyKeyboardMarkup(
    [[CANCEL_TEXT]], resize_keyboard=True, one_time_keyboard=True
)

LAST_NAME, FIRST_NAME, ORGANIZATION = range(3)

USER_KEYBOARD = ReplyKeyboardMarkup(
    [["🔍 Взять книгу", "📤 Вернуть книгу"], ["📚 Мои книги"], ["📖 Все книги"]],
    resize_keyboard=True,
)
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [["➕ Добавить книгу", "📊 Отчёт по библиотеке"], ["🔁 Сброс книги", "👤 Список пользователей"], ["📖 Все книги"]],
    resize_keyboard=True,
)


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle action cancellation and show the main menu."""
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id) else USER_KEYBOARD
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
        keyboard = ADMIN_KEYBOARD if is_admin(user_id) else USER_KEYBOARD
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
        "Введите организацию:", reply_markup=CANCEL_KEYBOARD
    )
    return ORGANIZATION


async def get_organization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    org = update.message.text.strip()
    register_user(
        user_id,
        context.user_data.get("first_name", ""),
        context.user_data.get("last_name", ""),
        org,
    )
    keyboard = ADMIN_KEYBOARD if is_admin(user_id) else USER_KEYBOARD
    await update.message.reply_text(
        "✅ Регистрация успешна.", reply_markup=keyboard
    )
    return ConversationHandler.END


def get_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_last_name)],
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_first_name)],
            ORGANIZATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_organization)],
        },
        fallbacks=[MessageHandler(filters.Regex(CANCEL_RE), cancel_action)],
    )


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the main menu keyboard based on user role."""
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id) else USER_KEYBOARD
    await update.message.reply_text("Главное меню", reply_markup=keyboard)


def get_menu_handler() -> CommandHandler:
    """Return handler for the /menu command."""
    return CommandHandler("menu", main_menu)

