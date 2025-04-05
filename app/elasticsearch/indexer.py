from typing import List, Dict, Any, Optional
from ..database.database import SessionLocal
from ..models.product import Product
from .es_client import get_es_client, PRODUCT_INDEX, PRODUCT_MAPPING
from .cache_manager import cache_search_results
from datetime import timedelta

BATCH_SIZE = 1000

def optimize_index():
    """Elasticsearch index'ini optimize et"""
    es = get_es_client()
    if not es:
        return False

    try:
        # Index ayarlarını optimize et
        es.indices.put_settings(
            index=PRODUCT_INDEX,
            body={
                "index": {
                    "refresh_interval": "30s",
                    "number_of_replicas": 0,
                    "translog.durability": "async",
                    "max_result_window": 50000
                }
            }
        )
        return True
    except Exception as e:
        print(f"Index optimizasyon hatası: {e}")
        return False

def bulk_index_products():
    """Veritabanındaki ürünleri batch halinde Elasticsearch'e aktar"""
    es = get_es_client()
    if not es:
        print("Elasticsearch bağlantısı kurulamadı")
        return False

    # İndeksi oluştur veya güncelle
    if es.indices.exists(index=PRODUCT_INDEX):
        es.indices.delete(index=PRODUCT_INDEX)
    es.indices.create(index=PRODUCT_INDEX, body=PRODUCT_MAPPING)

    # Optimize et
    optimize_index()

    # Veritabanından ürünleri al
    db = SessionLocal()
    try:
        # Toplam ürün sayısını al
        total_products = db.query(Product).count()
        print(f"Toplam {total_products} ürün indexlenecek")

        # Batch processing
        offset = 0
        while offset < total_products:
            products = db.query(Product).offset(offset).limit(BATCH_SIZE).all()
            if not products:
                break

            # Bulk data hazırla
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
                # Bulk indexing
                es.bulk(operations=bulk_data, refresh=True)
                print(f"{len(products)} ürün indexlendi (offset: {offset})")

            offset += BATCH_SIZE

        print(f"Toplam {offset} ürün başarıyla indexlendi")
        return True

    except Exception as e:
        print(f"Bulk indexing hatası: {e}")
        return False
    finally:
        db.close()

@cache_search_results(ttl=timedelta(hours=1))
def search_products(query: str, filters: Dict[str, Any] = None, size: int = 300000) -> List[Dict]:
    """
    Elasticsearch'te ürün araması yapar
    """
    es = get_es_client()
    if not es:
        return []

    # Query kontrolü
    if not query or not isinstance(query, str):
        query = "*"  # Eğer query None veya string değilse, tüm ürünleri getir

    # Base query - multi_match ile arama
    if query == "*":
        must_conditions = [{"match_all": {}}]
    else:
        must_conditions = [{
            "multi_match": {
                "query": query,
                "fields": ["brand^2", "model^2", "category", "description"],
                "fuzziness": "AUTO",
                "operator": "and"
            }
        }]

    # Filtreleri ekle
    if filters:
        if filters.get("category"):
            must_conditions.append({"term": {"category.keyword": filters["category"]}})
        
        if filters.get("brand"):
            must_conditions.append({"term": {"brand.keyword": filters["brand"]}})
        
        if filters.get("target_audience"):
            must_conditions.append({"term": {"target_audience.keyword": filters["target_audience"]}})
        
        # Fiyat filtresi
        price_range = {}
        if filters.get("min_price") is not None:
            price_range["gte"] = float(filters["min_price"])
        if filters.get("max_price") is not None:
            price_range["lte"] = float(filters["max_price"])
        
        if price_range:
            must_conditions.append({"range": {"price": price_range}})

    try:
        print(f"[DEBUG] Elasticsearch query: {must_conditions}")
        response = es.search(
            index=PRODUCT_INDEX,
            body={
                "query": {
                    "bool": {
                        "must": must_conditions
                    }
                },
                "size": min(size, 100),  # Maksimum 100 sonuç getir
                "sort": [
                    {"_score": "desc"},
                    {"price": "asc"}
                ],
                "_source": ["brand", "model", "price", "category", "description", "target_audience"]
            }
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