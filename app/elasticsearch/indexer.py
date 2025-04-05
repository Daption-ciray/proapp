from typing import List, Dict, Any
from ..database.database import SessionLocal
from ..models.product import Product
from .es_client import get_es_client, PRODUCT_INDEX, PRODUCT_MAPPING

def index_products():
    """Veritabanındaki ürünleri Elasticsearch'e aktarır"""
    es = get_es_client()
    if not es:
        print("Elasticsearch bağlantısı kurulamadı")
        return False

    # İndeksi oluştur veya güncelle
    if es.indices.exists(index=PRODUCT_INDEX):
        es.indices.delete(index=PRODUCT_INDEX)
    es.indices.create(index=PRODUCT_INDEX, body=PRODUCT_MAPPING)

    # Veritabanından ürünleri al
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        
        # Bulk indexing için veriyi hazırla
        bulk_data = []
        for product in products:
            # Index action
            bulk_data.append({
                "index": {
                    "_index": PRODUCT_INDEX,
                    "_id": product.id
                }
            })
            # Document
            bulk_data.append({
                "id": product.id,
                "brand": product.brand,
                "model": product.model,
                "price": product.price,
                "category": product.category,
                "target_audience": product.target_audience,
                "description": product.description,
                "suggest": {
                    "input": [
                        product.brand,
                        product.model,
                        product.category
                    ]
                }
            })

        if bulk_data:
            es.bulk(operations=bulk_data, refresh=True)
            print(f"{len(products)} ürün başarıyla indexlendi")
            return True

    except Exception as e:
        print(f"Indexleme hatası: {e}")
        return False
    finally:
        db.close()

def search_products(query: str, filters: Dict[str, Any] = None, size: int = 300000) -> List[Dict]:
    """
    Elasticsearch'te ürün araması yapar
    """
    es = get_es_client()
    if not es:
        return []

    # Source filtering - sadece gerekli alanları getir
    _source = ["brand", "model", "price", "category", "description", "target_audience"]

    # Base query optimization
    if query and query.strip():
        search_query = {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["brand^3", "model^2", "category^2", "description"],
                            "type": "most_fields",
                            "operator": "or",
                            "fuzziness": "AUTO",
                            "prefix_length": 2
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
    else:
        search_query = {"match_all": {}}

    # Filtreleri optimize et
    if filters:
        filter_list = []
        
        # Term queries için keyword field kullan
        if filters.get("category"):
            filter_list.append({"term": {"category.keyword": filters["category"]}})
        
        if filters.get("brand"):
            filter_list.append({"term": {"brand.keyword": filters["brand"]}})
        
        if filters.get("target_audience"):
            filter_list.append({"term": {"target_audience.keyword": filters["target_audience"]}})
        
        # Fiyat filtresi
        min_price = filters.get("min_price")
        max_price = filters.get("max_price")
        
        if min_price is not None or max_price is not None:
            price_range = {}
            if min_price is not None:
                price_range["gte"] = float(min_price)
            if max_price is not None:
                price_range["lte"] = float(max_price)
            
            if price_range:
                filter_list.append({"range": {"price": price_range}})

    # Optimize edilmiş sorgu yapısı
    final_query = {
        "bool": {
            "must": search_query if isinstance(search_query, dict) and "bool" not in search_query else [search_query],
            "filter": filter_list if filters and filter_list else []
        }
    }

    try:
        # Track_total_hits'i false yaparak sayım performansını artır
        response = es.search(
            index=PRODUCT_INDEX,
            query=final_query,
            _source=_source,
            size=min(size, 100),  # İlk sayfada maksimum 100 sonuç getir
            track_total_hits=False,
            sort=[{"_score": "desc"}, {"price": "asc"}]
        )
        
        return [hit["_source"] for hit in response["hits"]["hits"]]

    except Exception as e:
        print(f"Arama hatası: {e}")
        return []

def get_suggestions(prefix: str, field: str = "suggest") -> List[str]:
    """Otomatik tamamlama önerileri alır"""
    es = get_es_client()
    if not es:
        return []

    try:
        response = es.search(
            index=PRODUCT_INDEX,
            body={
                "suggest": {
                    "product_suggest": {
                        "prefix": prefix,
                        "completion": {
                            "field": field,
                            "size": 5,
                            "skip_duplicates": True
                        }
                    }
                }
            }
        )
        
        suggestions = response["suggest"]["product_suggest"][0]["options"]
        return [suggestion["text"] for suggestion in suggestions]

    except Exception as e:
        print(f"Öneri alma hatası: {e}")
        return [] 