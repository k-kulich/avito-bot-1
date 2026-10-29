import asyncio
from typing import List, Callable
import logging
from datetime import datetime
from sqlalchemy import select
from lib.core.database import AsyncSessionLocal
from lib.models.search_query import SearchQuery
from lib.models.user import User
from lib.services.ad_service import is_ad_sent, mark_ad_sent
from lib.parser.avito_parser import AvitoMonitor
from lib.data_classes import AdItem

logger = logging.getLogger(__name__)

class MonitorManager:
    def __init__(self):
        self.monitor = AvitoMonitor()
        self.callbacks: List[Callable] = []

    async def start(self):
        await self.monitor.start()

    async def stop(self):
        await self.monitor.stop()

    async def run_monitoring_cycle(self):
        async with AsyncSessionLocal() as session:
            # Получаем все активные запросы активных пользователей
            # Примечание: если у нескольких пользователей одинаковые параметры запроса,
            # они будут дублироваться в списке, чтобы каждому проверить отдельно.
            # Это упрощает логику, но можно оптимизировать.
            result = await session.execute(
                select(SearchQuery)
                .join(User)
                .where(User.is_active == True, SearchQuery.is_active == True)
            )
            queries = result.scalars().all()

            # Группируем запросы по пользователям (можно и по параметрам, но оставим так)
            for db_query in queries:
                # Преобразуем в датакласс для парсера
                query_dc = db_query.to_dataclass()
                ads = await self.monitor.search_ads(query_dc)
                for ad in ads:
                    # Проверяем, отправляли ли уже это объявление данному пользователю
                    if not await is_ad_sent(session, db_query.user_id, ad.id):
                        # Уведомляем
                        for callback in self.callbacks:
                            await callback(db_query.user_id, ad)
                        # Помечаем как отправленное
                        await mark_ad_sent(session, db_query.user_id, ad.id, ad.url)
            logger.info("Цикл мониторинга завершён")

    async def start_continuous_monitoring(self, interval: int = 300):
        while True:
            try:
                start = datetime.now()
                await self.run_monitoring_cycle()
                elapsed = (datetime.now() - start).total_seconds()
                await asyncio.sleep(max(10, interval - elapsed))
            except asyncio.CancelledError:
                logger.info("Мониторинг остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка в мониторинге: {e}")
                await asyncio.sleep(60)

    def add_callback(self, callback: Callable):
        self.callbacks.append(callback)