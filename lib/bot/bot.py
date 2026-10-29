from telegram.ext import Application
import asyncio
from lib.core.config import TELEGRAM_TOKEN
from lib.core.database import AsyncSessionLocal
from lib.monitor.monitor_manager import MonitorManager
from .handlers import setup_handlers
from .keyboards import main_keyboard

class AvitoBot:
    def __init__(self):
        self.db_session_factory = AsyncSessionLocal
        self.monitor_manager = MonitorManager()
        self.application = Application.builder().token(TELEGRAM_TOKEN).build()
        self.main_keyboard = main_keyboard()
        setup_handlers(self.application, self)

    async def send_ad_notification(self, chat_id: int, ad):
        # ad – объект AdItem
        await self.application.bot.send_message(
            chat_id=chat_id,
            text=ad.to_message(),
            parse_mode='Markdown'
        )

    async def run(self):
        self.monitor_manager.add_callback(self.send_ad_notification)
        # Запуск мониторинга в фоне
        asyncio.create_task(self.monitor_manager.start_continuous_monitoring())

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        # Бесконечное ожидание
        while True:
            await asyncio.sleep(1)