import random
import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import hashlib

from lib.data_classes import SearchQueryDC, AdItemDC
from lib.core.config import CHANGE_IP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AvitoMonitor:
    """Асинхронный монитор объявлений Avito"""
    
    BASE_URL = "https://www.avito.ru"
    API_ITEMS_URL = "https://www.avito.ru/api/9/items"
    API_PHONE_URL = "https://www.avito.ru/api/1/items/{}/phone"
    REGIONS = "https://rest-app.net/api/region"
    CITIES = "https://rest-app.net/api/city"
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or []
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers_pool = self._generate_headers_pool()
        
    def _generate_headers_pool(self) -> List[Dict[str, str]]:
        """Генерация пула различных заголовков"""
        return [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
        ]
    
    async def start(self):
        """Запуск сессии"""
        self.session = aiohttp.ClientSession()
        logger.info("Сессия запущена")
    
    async def stop(self):
        """Остановка сессии"""
        if self.session:
            await self.session.close()
            logger.info("Сессия остановлена")
    
    def _get_proxy(self) -> Optional[str]:
        """Получение случайного прокси из списка"""
        if not self.proxy_list:
            return None
        return random.choice(self.proxy_list)
    
    def _get_headers(self) -> Dict[str, str]:
        """Получение случайных заголовков"""
        return random.choice(self.headers_pool)

    async def _make_request(self, url: str, method: str = "GET", params: Dict = None, json_data: Dict = None, max_retries: int = 4) -> Optional[str]:
        """Выполнение HTTP запроса с прокси и повторными попытками"""
        for attempt in range(max_retries):
            try:
                proxy = self._get_proxy()
                headers = self._get_headers()
                
                timeout = aiohttp.ClientTimeout(total=50)
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    proxy=proxy,
                    timeout=timeout,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        return await response.text()
                    # elif response.status == 403:
                    #     logger.warning(f"Доступ запрещен (403) для {url}")
                    #     await asyncio.sleep(2 ** attempt)  # Экспоненциальная задержка
                    # elif response.status == 429:
                    #     logger.warning(f"Слишком много запросов (429) для {url}")
                    #     await asyncio.sleep(5 * (attempt + 1))
                    # else:
                    #     logger.warning(f"Ошибка {response.status} для {url}")
                        
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка соединения: {e}")
            except asyncio.TimeoutError as e:
                logger.error(f"Таймаут для {url}: {e}")
            logger.warning("Ошибка. Меняю IP.")
            await self.session.get(CHANGE_IP, proxy=proxy, timeout=30)

            await asyncio.sleep(random.uniform(1, 3))
        
        logger.error(f"Не удалось выполнить запрос к {url} после {max_retries} попыток")
        return None
    
    async def search_ads(self, query: SearchQueryDC, limit: int = 50) -> List[AdItemDC]:
        """Поиск объявлений по параметрам с использованием ID категории"""
        search_url = query.get_url()
        html = await self._make_request(search_url)
        if not html:
            logger.info('no html')
            return []
        
        ads = await self._parse_search_page(html, query.city_slug, query.query_string)
        # Убрана фильтрация по self.processed_ads
        return ads[:limit]
    
    async def _parse_search_page(self, html: str, city_slug: str, category_id: str) -> List[AdItemDC]:
        """Парсинг страницы с результатами поиска"""
        soup = BeautifulSoup(html, 'html.parser')
        ads = []
        
        ad_blocks = soup.select('div[data-marker="item"]')
        
        for block in ad_blocks:
            try:
                # Заголовок
                title_elem = block.select_one('a[data-marker="item-title"]')
                title = title_elem.text.strip() if title_elem else "Без названия"
                
                # Ссылка
                link_elem = block.select_one('a[data-marker="item-title"]')
                if not link_elem:
                    continue
                    
                ad_url = f"{self.BASE_URL}{link_elem.get('href', '')}"
                ad_id = self._extract_id_from_url(ad_url)
                
                # Цена
                price_elem = block.select_one('meta[itemprop="price"]')
                price_content = price_elem.get('content') if price_elem else None
                price = int(price_content) if price_content and price_content.isdigit() else None
                
                # Описание
                desc_elem = block.select_one('div[class*="description"]')
                description = desc_elem.text.strip() if desc_elem else ""
                
                # Адрес
                address_elem = block.select_one('div[data-marker="item-address"]')
                address = address_elem.text.strip() if address_elem else None
                
                # Продавец
                seller_elem = block.select_one('div[data-marker="seller-info/name"]')
                seller = seller_elem.text.strip() if seller_elem else None
                
                # Картинки
                images = []
                img_elements = block.select('img[data-marker="item-photo"]')
                for img in img_elements:
                    src = img.get('src') or img.get('data-src')
                    if src and src.startswith('http'):
                        images.append(src)
                
                # Время публикации
                time_elem = block.select_one('div[data-marker="item-date"]')
                timestamp = self._parse_timestamp(time_elem.text.strip() if time_elem else "")
                
                ad = AdItemDC(
                    id=ad_id,
                    title=title,
                    price=price,
                    url=ad_url,
                    description=description,
                    city_slug=city_slug,
                    category_param=category_id,
                    address=address,
                    seller=seller,
                    phone=None,
                    images=images,
                    timestamp=timestamp,
                    metadata={
                        'parsed_at': datetime.now().isoformat(),
                        'source': 'avito',
                        'has_images': len(images) > 0
                    }
                )
                
                ads.append(ad)
                
            except Exception as e:
                logger.error(f"Ошибка парсинга блока объявления: {e}")
                continue
        
        logger.info(f"Спаршено {len(ads)} объявлений для {city_slug}/{category_id}")
        return ads
    
    def _extract_id_from_url(self, url: str) -> str:
        """Извлечение ID объявления из URL"""
        import re
        match = re.search(r'(\d+)$', url)
        return match.group(1) if match else hashlib.md5(url.encode()).hexdigest()[:10]
    
    def _parse_timestamp(self, time_str: str) -> datetime:
        """Парсинг времени из строки Avito"""
        now = datetime.now()
        if 'сегодня' in time_str.lower():
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'вчера' in time_str.lower():
            from datetime import timedelta
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            try:
                from dateutil import parser
                return parser.parse(time_str, dayfirst=True)
            except:
                return now

    async def get_ad_details(self, ad: AdItemDC) -> AdItemDC:
        """Получение детальной информации об объявлении"""
        html = await self._make_request(ad.url)
        if not html:
            return ad
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            phone_script = soup.find('script', string=lambda x: x and 'phone' in x.lower())
            if phone_script:
                import re
                phone_match = re.search(r'(\+7|8)[\s\-\(\)]?\d{3}[\s\-\(\)]?\d{3}[\s\-\(\)]?\d{2}[\s\-\(\)]?\d{2}', phone_script.text)
                if phone_match:
                    ad.phone = phone_match.group(0)
            views_elem = soup.select_one('span[data-marker="item-view/total-views"]')
            if views_elem:
                views_text = views_elem.text.strip()
                import re
                views_match = re.search(r'(\d+)', views_text.replace(' ', ''))
                if views_match:
                    ad.views_total = int(views_match.group(1))
            map_script = soup.find('script', string=lambda x: x and 'coordinates' in x.lower() if x else False)
            if map_script:
                import json as json_module
                import re
                coords_match = re.search(r'coordinates["\']?\s*:\s*({[^}]+})', map_script.text)
                if coords_match:
                    try:
                        coords = json_module.loads(coords_match.group(1))
                        ad.lat = float(coords.get('lat', 0))
                        ad.lng = float(coords.get('lng', 0))
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Ошибка получения деталей объявления {ad.id}: {e}")
        
        return ad
    
    async def _get_regions_and_cities(self) -> None:
        """Сохранить данные обо всех регионах и городах в JSON файлы."""
        regions = await self._make_request(self.REGIONS)
        with open('data/all_regions.json', mode='w') as out:
            out.write(regions)
        cities = await self._make_request(self.CITIES)
        with open('data/all_cities.json', mode='w') as out:
            out.write(cities)