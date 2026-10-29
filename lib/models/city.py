from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from lib.core.database import Base

class City(Base, AsyncAttrs):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    region = Column(String, nullable=True)

    queries = relationship("SearchQuery", back_populates="city")