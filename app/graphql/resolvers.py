from typing import List, Optional
import strawberry
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..schemas.product import Product, ProductFilter, ProductStats, SearchResult, SearchFilter
from ..models.product import Product as ProductModel
from ..database.database import get_db
from ..elasticsearch.indexer import search_products, get_suggestions

def get_db_context():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

@strawberry.type
class Query:
    @strawberry.field
    def search(self, query: str, filter: Optional[SearchFilter] = None) -> List[SearchResult]:
        """Elasticsearch ile ürün araması yapar"""
        filters = {}
        if filter:
            if filter.category:
                filters["category"] = filter.category
            if filter.brand:
                filters["brand"] = filter.brand
            if filter.target_audience:
                filters["target_audience"] = filter.target_audience
            if filter.min_price is not None and filter.max_price is not None:
                filters["price_range"] = (filter.min_price, filter.max_price)
        
        results = search_products(query, filters)
        return [
            SearchResult(
                id=result["id"],
                brand=result["brand"],
                model=result["model"],
                price=result["price"],
                category=result["category"],
                target_audience=result["target_audience"],
                description=result["description"],
                score=result.get("score", 0.0)
            )
            for result in results
        ]

    @strawberry.field
    def suggest(self, prefix: str) -> List[str]:
        """Otomatik tamamlama önerileri döndürür"""
        return get_suggestions(prefix)

    @strawberry.field
    def products(self, filter: Optional[ProductFilter] = None) -> List[Product]:
        """PostgreSQL'den ürün listesi döndürür"""
        db = next(get_db_context())
        query = db.query(ProductModel)
        
        if filter:
            if filter.brand:
                query = query.filter(ProductModel.brand == filter.brand)
            if filter.category:
                query = query.filter(ProductModel.category == filter.category)
            if filter.target_audience:
                query = query.filter(ProductModel.target_audience == filter.target_audience)
            if filter.min_price is not None:
                query = query.filter(ProductModel.price >= filter.min_price)
            if filter.max_price is not None:
                query = query.filter(ProductModel.price <= filter.max_price)
        
        return query.all()

    @strawberry.field
    def product(self, id: int) -> Optional[Product]:
        db = next(get_db_context())
        return db.query(ProductModel).filter(ProductModel.id == id).first()

    @strawberry.field
    def product_stats(self) -> List[ProductStats]:
        """Ürün istatistiklerini döndürür"""
        db = next(get_db_context())
        stats = db.query(
            ProductModel.category,
            func.count(ProductModel.id).label('count'),
            func.avg(ProductModel.price).label('avg_price'),
            func.min(ProductModel.price).label('min_price'),
            func.max(ProductModel.price).label('max_price')
        ).group_by(ProductModel.category).all()
        
        return [
            ProductStats(
                category=stat.category,
                count=stat.count,
                avg_price=float(stat.avg_price),
                min_price=float(stat.min_price),
                max_price=float(stat.max_price)
            )
            for stat in stats
        ] 