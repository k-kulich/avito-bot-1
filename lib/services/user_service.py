from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from lib.models.user import User

async def get_user(session: AsyncSession, chat_id: int) -> User | None:
    result = await session.execute(select(User).where(User.chat_id == chat_id))
    return result.scalar_one_or_none()

async def create_user(session: AsyncSession, chat_id: int, username: str, first_name: str) -> User:
    user = User(chat_id=chat_id, username=username, first_name=first_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def update_user(session: AsyncSession, chat_id: int, **kwargs):
    user = await get_user(session, chat_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        await session.commit()

async def get_active_users(session: AsyncSession):
    result = await session.execute(select(User).where(User.is_active == True))
    return result.scalars().all()