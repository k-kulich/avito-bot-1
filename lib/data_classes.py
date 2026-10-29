from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import hashlib
from urllib.parse import quote


@dataclass_json
@dataclass
class SearchQueryDC:
    """Параметры поискового запроса пользователя (упрощённая версия)"""
    city_slug: str
    query_string: str
    query_id: str = field(default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    is_active: bool = True

    def get_url(self) -> str:
        """Генерация полного URL для Avito"""
        base_url = "https://www.avito.ru"
        encoded_query = quote(self.query_string, safe="")
        return f"{base_url}/{self.city_slug}?q={encoded_query}"

    def to_key(self) -> str:
        """Уникальный ключ для запроса (используется для группировки)"""
        return hashlib.md5(f"{self.city_slug}_{self.query_string}".encode()).hexdigest()

    @classmethod
    def from_model(cls, model):
        """Преобразует модель SQLAlchemy в датакласс."""
        return cls(
            city_slug=model.city.slug,
            query_string=model.query_string,
            query_id=model.id,
            is_active=model.is_active
        )

@dataclass_json
@dataclass 
class SearchQueryOld:
    """Параметры поискового запроса пользователя"""
    category_param: str
    city_slug: str  # slug города
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    rooms: Optional[List[int]] = None
    query_id: str = field(default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    is_active: bool = True
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    def get_url(self) -> str:
        """Генерация полного URL для Avito"""
        base_url = "https://www.avito.ru"
        
        encoded_category = self.category_param.replace(' ', '+')
        
        url = f"{base_url}/{self.city_slug}"
        
        params = self.get_params()
        if params:
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{param_str}&q={encoded_category}"
        print(url)
        return url
    
    def to_new_sq(self) -> SearchQueryDC:
        return SearchQueryDC(city_slug=self.city_slug, query_string=self.category_param, 
                             query_id=self.query_id, is_active=self.is_active)

@dataclass_json
@dataclass
class AdItemDC:
    """Объявление с Avito (без изменений)"""
    # ... (поля остаются как раньше)
    id: str
    title: str
    price: Optional[int]
    url: str
    description: str
    city_slug: str
    category_param: str   # здесь можно хранить исходный query_string, но для совместимости оставим
    address: Optional[str]
    seller: Optional[str]
    phone: Optional[str]
    images: List[str]
    timestamp: datetime
    query_key: str
    views_total: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_category_id(self) -> bool:
        return False  # больше не используется

    def to_message(self, city_name: str = None, category_name: str = None) -> str:
        # без изменений, но category_name можно не передавать
        pass