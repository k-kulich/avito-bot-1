from telegram import Update
from telegram.ext import ContextTypes
from lib.services.city_service import search_cities, get_city_by_id
from lib.services.query_service import create_query, get_user_queries, toggle_query
from .keyboards import main_keyboard, city_choice_keyboard

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, bot):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "add_query":
        await query.edit_message_text("📝 *Создание запроса*\n\nВведите город:", parse_mode='Markdown')
        context.user_data['await_city'] = True

    elif data == "list_queries":
        chat_id = update.effective_chat.id
        async with bot.db_session_factory() as session:
            queries = await get_user_queries(session, chat_id)
            if not queries:
                await query.edit_message_text("У вас нет запросов.", reply_markup=main_keyboard())
                return
            text = "📋 *Ваши запросы:*\n"
            for q in queries:
                status = "✅" if q.is_active else "⏸️"
                city_name = q.city.title if q.city else "Не указан"
                text += f"\n{status} {city_name} – {q.category_param}"
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=main_keyboard())

    elif data.startswith("city_"):
        city_id = int(data[5:])
        async with bot.db_session_factory() as session:
            city = await get_city_by_id(session, city_id)
            if city:
                context.user_data['city_id'] = city.id
                context.user_data['city_slug'] = city.slug
                context.user_data['city_title'] = city.title
                context.user_data['await_city'] = False
                context.user_data['await_category'] = True
                await query.edit_message_text(f"✅ Город: {city.title}\n\nТеперь введите категорию:")
            else:
                await query.edit_message_text("Ошибка выбора города.", reply_markup=main_keyboard())

    elif data.startswith("toggle_"):
        query_id = data[7:]
        chat_id = update.effective_chat.id
        async with bot.db_session_factory() as session:
            new_state = await toggle_query(session, query_id, chat_id)
            if new_state is not None:
                await query.answer(f"Запрос {'включён' if new_state else 'выключен'}")
            else:
                await query.answer("Ошибка")
        # Обновляем список запросов
        await button_handler(update, context, bot)  # рекурсивно вызываем с data = "list_queries"