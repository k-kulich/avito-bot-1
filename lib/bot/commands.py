from telegram import Update
from telegram.ext import ContextTypes
from lib.services.user_service import get_user, create_user, update_user
from .keyboards import main_keyboard
from .messages import START_MESSAGE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, bot):
    chat_id = update.effective_chat.id
    username = update.effective_user.username or str(chat_id)
    first_name = update.effective_user.first_name

    async with bot.db_session_factory() as session:
        user = await get_user(session, chat_id)
        if not user:
            user = await create_user(session, chat_id, username, first_name)
        elif not user.is_active:
            user.is_active = True
            await session.commit()

    await update.message.reply_text(
        START_MESSAGE.format(first_name=first_name),
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE, bot):
    chat_id = update.effective_chat.id
    async with bot.db_session_factory() as session:
        user = await get_user(session, chat_id)
        if user and user.is_active:
            user.is_active = False
            await session.commit()
            await update.message.reply_text("Вы отписались от уведомлений.")
        else:
            await update.message.reply_text("Вы не подписаны.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE, bot):
    chat_id = update.effective_chat.id
    async with bot.db_session_factory() as session:
        user = await get_user(session, chat_id)
        if user:
            status_text = "активна" if user.is_active else "неактивна"
            await update.message.reply_text(f"Статус подписки: {status_text}")
        else:
            await update.message.reply_text("Вы не зарегистрированы.")