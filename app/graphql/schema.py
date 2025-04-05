import strawberry
from typing import List, Optional
from ..models.product import Product as ProductModel
from ..elasticsearch.es_client import get_es_client, PRODUCT_INDEX
from elasticsearch import NotFoundError

@strawberry.type
class Product:
    id: int
    brand: str
    model: str
    price: float
    category: str
    target_audience: str
    description: str

@strawberry.type
class ProductSuggestions:
    suggestions: List[str]

@strawberry.type
class Query:
    @strawberry.field
    def products(self) -> List[Product]:
        # Existing products query implementation
        pass

    @strawberry.field
    def search_products(
        self, 
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 20
    ) -> List[Product]:
        es = get_es_client()
        if not es:
            return []

        # Build search query
        must_conditions = [{
            "multi_match": {
                "query": query,
                "fields": ["brand^2", "model^2", "category", "description"],
                "fuzziness": "AUTO"
            }
        }]

        # Add filters if provided
        if category:
            must_conditions.append({"term": {"category": category}})
        
        range_filter = {}
        if min_price is not None:
            range_filter["gte"] = min_price
        if max_price is not None:
            range_filter["lte"] = max_price
        
        if range_filter:
            must_conditions.append({"range": {"price": range_filter}})

        # Execute search
        try:
            response = es.search(
                index=PRODUCT_INDEX,
                body={
                    "query": {
                        "bool": {
                            "must": must_conditions
                        }
                    },
                    "size": limit
                }
            )
            
            # Convert results to Product types
            products = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                products.append(
                    Product(
                        id=source.get("id", 0),
                        brand=source["brand"],
                        model=source["model"],
                        price=source["price"],
                        category=source["category"],
                        target_audience=source["target_audience"],
                        description=source["description"]
                    )
                )
            return products
        except Exception as e:
            print(f"Search error: {e}")
            return []

    @strawberry.field
    def suggest_products(self, prefix: str, limit: int = 5) -> ProductSuggestions:
        es = get_es_client()
        if not es:
            return ProductSuggestions(suggestions=[])

        try:
            response = es.search(
                index=PRODUCT_INDEX,
                body={
                    "suggest": {
                        "product_suggestions": {
                            "prefix": prefix,
                            "completion": {
                                "field": "suggest",
                                "size": limit,
                                "skip_duplicates": True
                            }
                        }
                    }
                }
            )
            
            suggestions = []
            for suggestion_group in response["suggest"]["product_suggestions"]:
                for option in suggestion_group["options"]:
                    suggestions.append(option["text"])
            
            return ProductSuggestions(suggestions=suggestions)
        except Exception as e:
            print(f"Suggestion error: {e}")
            return ProductSuggestions(suggestions=[])

# GraphQL şemasını oluştur
schema = strawberry.Schema(query=Query) 