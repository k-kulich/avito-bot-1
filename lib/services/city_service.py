import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lib.models.city import City

async def init_cities(session: AsyncSession):
    """Загружает города из JSON в БД, если таблица пуста."""
    result = await session.execute(select(City).limit(1))
    if result.scalar_one_or_none():
        return
    with open("data/all_cities.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        cities_data = data.get("data", data) if isinstance(data, dict) else data
    for item in cities_data:
        slug = item.get("slug") or _generate_slug(item["name"])
        city = City(
            slug=slug,
            title=item["name"],
            region=item.get("region")
        )
        session.add(city)
    await session.commit()

def _generate_slug(name: str) -> str:
    # упрощённая транслитерация
    translit = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e',
                'ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m',
                'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
                'ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
                'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',' ':'-'}
    return ''.join(translit.get(c, c) for c in name.lower())

async def search_cities(session: AsyncSession, query: str, limit: int = 10):
    result = await session.execute(
        select(City).where(City.title.ilike(f"%{query}%")).limit(limit)
    )
    return result.scalars().all()

async def get_city_by_slug(session: AsyncSession, slug: str):
    result = await session.execute(select(City).where(City.slug == slug))
    return result.scalar_one_or_none()

async def get_city_by_id(session: AsyncSession, city_id: int):
    return await session.get(City, city_id)