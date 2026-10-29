from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from lib.core.database import Base

class SentAd(Base, AsyncAttrs):
    __tablename__ = "sent_ads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.chat_id"), nullable=False)
    ad_id = Column(String, nullable=False)        # ID объявления с Avito
    ad_url = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="sent_ads")