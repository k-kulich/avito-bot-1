from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lib.models.search_query import SearchQuery
import hashlib
from datetime import datetime

async def get_user_queries(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(SearchQuery).where(SearchQuery.user_id == user_id)
    )
    return result.scalars().all()

async def create_query(session: AsyncSession, user_id: int, city_id: int, query_string: str) -> SearchQuery:
    query_id = hashlib.md5(f"{user_id}{city_id}{query_string}{datetime.now()}".encode()).hexdigest()[:8]
    query = SearchQuery(
        id=query_id,
        user_id=user_id,
        city_id=city_id,
        query_string=query_string,
        is_active=True
    )
    session.add(query)
    await session.commit()
    await session.refresh(query)
    return query

async def toggle_query(session: AsyncSession, query_id: str, user_id: int):
    query = await session.get(SearchQuery, query_id)
    if query and query.user_id == user_id:
        query.is_active = not query.is_active
        await session.commit()
        return query.is_active
    return None

async def delete_query(session: AsyncSession, query_id: str, user_id: int):
    query = await session.get(SearchQuery, query_id)
    if query and query.user_id == user_id:
        await session.delete(query)
        await session.commit()
        return True
    return False