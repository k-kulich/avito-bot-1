from telegram import Update
from telegram.ext import ContextTypes
from lib.services.city_service import search_cities
from lib.services.query_service import create_query
from .keyboards import city_choice_keyboard, main_keyboard

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, bot):
    if context.user_data.get('await_city'):
        city_input = update.message.text.strip()
        async with bot.db_session_factory() as session:
            cities = await search_cities(session, city_input)
            if not cities:
                await update.message.reply_text("Город не найден. Попробуйте снова.")
                return
            if len(cities) == 1:
                city = cities[0]
                context.user_data['city_id'] = city.id
                context.user_data['city_slug'] = city.slug
                context.user_data['city_title'] = city.title
                context.user_data['await_city'] = False
                context.user_data['await_category'] = True
                await update.message.reply_text(f"✅ Город: {city.title}\n\nТеперь введите категорию:")
            else:
                await update.message.reply_text(
                    "Найдено несколько городов. Выберите:",
                    reply_markup=city_choice_keyboard(cities)
                )
                context.user_data['await_city_selection'] = True
        return

    # В messages.py (handle_message) после выбора города:
    if context.user_data.get('await_category'):
        query_string = update.message.text.strip()
        city_id = context.user_data.get('city_id')
        chat_id = update.effective_chat.id
        async with bot.db_session_factory() as session:
            await create_query(session, chat_id, city_id, query_string)
        context.user_data.clear()
        await update.message.reply_text("✅ Запрос создан!", reply_markup=main_keyboard())
        return

    await update.message.reply_text("Используйте кнопки меню.", reply_markup=main_keyboard())


START_MESSAGE = """
👋 Привет, {first_name}!

Я бот для мониторинга объявлений на Avito.

📋 *Что я умею:*
• Мониторить новые объявления по вашим запросам
• Уведомлять о новых предложениях
• Хранить историю просмотренных объявлений

📝 *Как начать:*
1. Нажмите '➕ Добавить запрос'
2. Укажите город и категорию
3. Я начну отправлять уведомления о новых объявлениях!
"""

HELP_MESSAGE = """
❓ *Помощь*

*Основные команды:*
• /start - Запустить бота
• /stop - Остановить уведомления
• /status - Статус подписки

*Как добавить запрос:*
1. Нажмите '➕ Добавить запрос'
2. Введите город
3. Введите категорию
"""
# ... остальные сообщения