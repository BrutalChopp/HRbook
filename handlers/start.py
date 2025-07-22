from __future__ import annotations

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, ConversationHandler, MessageHandler, ContextTypes, filters

from utils import get_user, register_user, is_admin

LAST_NAME, FIRST_NAME, ORGANIZATION = range(3)

USER_KEYBOARD = ReplyKeyboardMarkup(
    [["🔍 Взять книгу", "📤 Вернуть книгу"], ["📚 Мои книги"]],
    resize_keyboard=True,
)
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [["➕ Добавить книгу", "📊 Отчёт по библиотеке"], ["🔁 Сброс книги", "👤 Список пользователей"]],
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user = get_user(user_id)
    if user:
        keyboard = ADMIN_KEYBOARD if is_admin(user_id) else USER_KEYBOARD
        await update.message.reply_text(
            "С возвращением!", reply_markup=keyboard
        )
        return ConversationHandler.END
    await update.message.reply_text("Добро пожаловать! Введите вашу фамилию:")
    return LAST_NAME


async def get_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["last_name"] = update.message.text.strip()
    await update.message.reply_text("Введите ваше имя:")
    return FIRST_NAME


async def get_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["first_name"] = update.message.text.strip()
    await update.message.reply_text("Введите организацию:")
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
        fallbacks=[],
    )


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the main menu keyboard based on user role."""
    keyboard = ADMIN_KEYBOARD if is_admin(update.effective_user.id) else USER_KEYBOARD
    await update.message.reply_text("Главное меню", reply_markup=keyboard)


def get_menu_handler() -> CommandHandler:
    """Return handler for the /menu command."""
    return CommandHandler("menu", main_menu)

