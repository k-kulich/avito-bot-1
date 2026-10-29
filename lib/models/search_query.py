from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from lib.core.database import Base

class SearchQuery(Base, AsyncAttrs):
    __tablename__ = "search_queries"

    id = Column(String, primary_key=True, index=True)          # генерируемый ID
    user_id = Column(Integer, ForeignKey("users.chat_id"), nullable=False)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=False)
    query_string = Column(String, nullable=False)              # то, что ввёл пользователь (например "квартиры +студии")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="queries")
    city = relationship("City", back_populates="queries")

    def to_dataclass(self):
        """Преобразование в датакласс для парсера"""
        from lib.data_classes import SearchQueryDC
        return SearchQueryDC(
            city_slug=self.city.slug,
            query_string=self.query_string,
            query_id=self.id,
            is_active=self.is_active
        )