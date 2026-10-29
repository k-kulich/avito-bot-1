from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from lib.core.database import Base

class User(Base, AsyncAttrs):
    __tablename__ = "users"

    chat_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_notified = Column(DateTime(timezone=True), nullable=True)

    queries = relationship("SearchQuery", back_populates="user", cascade="all, delete-orphan")
    sent_ads = relationship("SentAd", back_populates="user", cascade="all, delete-orphan")