from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lib.models.sent_ad import SentAd

async def is_ad_sent(session: AsyncSession, user_id: int, ad_id: str) -> bool:
    result = await session.execute(
        select(SentAd).where(SentAd.user_id == user_id, SentAd.ad_id == ad_id)
    )
    return result.first() is not None

async def mark_ad_sent(session: AsyncSession, user_id: int, ad_id: str, ad_url: str = None):
    sent = SentAd(user_id=user_id, ad_id=ad_id, ad_url=ad_url)
    session.add(sent)
    await session.commit()