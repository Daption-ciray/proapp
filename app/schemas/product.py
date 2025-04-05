from typing import Optional, List
import strawberry
from decimal import Decimal

@strawberry.type
class Product:
    id: int
    brand: str
    price: float
    category: str
    model: str
    target_audience: str
    description: str

@strawberry.type
class SearchResult(Product):
    score: float

@strawberry.input
class SearchFilter:
    category: Optional[str] = None
    brand: Optional[str] = None
    target_audience: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

@strawberry.input
class ProductFilter:
    brand: Optional[str] = None
    category: Optional[str] = None
    target_audience: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

@strawberry.type
class ProductStats:
    category: str
    count: int
    avg_price: float
    min_price: float
    max_price: float 