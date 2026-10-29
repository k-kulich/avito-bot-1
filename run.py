import asyncio
import logging
from lib.core.database import engine, AsyncSessionLocal
from lib.models import Base
from lib.services.city_service import init_cities
from lib.bot.bot import AvitoBot

logging.basicConfig(level=logging.INFO)

async def main():
    # Создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Загрузка городов
    async with AsyncSessionLocal() as session:
        await init_cities(session)

    # Запуск бота
    bot = AvitoBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())