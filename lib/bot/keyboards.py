from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить запрос", callback_data="add_query")],
        [InlineKeyboardButton("📋 Мои запросы", callback_data="list_queries")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
         InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ])

def city_choice_keyboard(cities):
    keyboard = []
    for city in cities[:5]:
        keyboard.append([InlineKeyboardButton(city.title, callback_data=f"city_{city.id}")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

# можно добавить другие клавиатуры (для запросов, подтверждений и т.д.)