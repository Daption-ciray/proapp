from ..database.database import SessionLocal
from ..models.product import Product
from ..elasticsearch.es_client import get_es_client, PRODUCT_INDEX, PRODUCT_MAPPING
import json
from typing import List, Dict
import time
from dotenv import load_dotenv
import os

# Force reload environment variables at script start
load_dotenv(override=True)
print(f"ELASTICSEARCH_URL in sync_data.py: {os.getenv('ELASTICSEARCH_URL')}")

def chunk_data(data: List[Dict], chunk_size: int = 5000):
    """Veriyi belirtilen boyutta parçalara ayır"""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def index_products_from_json(json_file: str = "products.json", chunk_size: int = 5000):
    """JSON dosyasından ürünleri Elasticsearch'e aktar"""
    es = get_es_client()
    if not es:
        print("Elasticsearch bağlantısı kurulamadı")
        return False

    try:
        # JSON dosyasını oku
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        print(f"Toplam {len(products)} ürün yüklenecek")
        
        # İndeksi oluştur veya güncelle
        if es.indices.exists(index=PRODUCT_INDEX):
            print(f"{PRODUCT_INDEX} indeksi siliniyor...")
            es.indices.delete(index=PRODUCT_INDEX)
        
        print(f"{PRODUCT_INDEX} indeksi oluşturuluyor...")
        es.indices.create(index=PRODUCT_INDEX, body=PRODUCT_MAPPING)
        
        # Bulk indexing için veriyi hazırla ve yükle
        start_time = time.time()
        total_indexed = 0
        
        for chunk in chunk_data(products, chunk_size):
            bulk_data = []
            for product in chunk:
                # Index action
                bulk_data.append({
                    "index": {
                        "_index": PRODUCT_INDEX,
                        "_id": product.get("id", None)
                    }
                })
                # Document
                product_doc = {
                    "brand": product["brand"],
                    "model": product["model"],
                    "price": product["price"],
                    "category": product["category"],
                    "target_audience": product["target_audience"],
                    "description": product["description"],
                    "suggest": {
                        "input": [
                            product["brand"],
                            product["model"],
                            product["category"]
                        ]
                    }
                }
                bulk_data.append(product_doc)
            
            # Bulk request gönder
            if bulk_data:
                es.bulk(operations=bulk_data, refresh=False)
                total_indexed += len(chunk)
                elapsed_time = time.time() - start_time
                docs_per_second = total_indexed / elapsed_time
                print(f"İlerleme: {total_indexed}/{len(products)} döküman ({docs_per_second:.2f} döküman/saniye)")
        
        # İndeksi yenile
        es.indices.refresh(index=PRODUCT_INDEX)
        
        total_time = time.time() - start_time
        print(f"\nToplam {total_indexed} ürün {total_time:.2f} saniyede yüklendi")
        print(f"Ortalama hız: {total_indexed/total_time:.2f} döküman/saniye")
        
        return True

    except Exception as e:
        print(f"İndeksleme hatası: {e}")
        return False

if __name__ == "__main__":
    # Önce örnek verileri oluştur
    from ..scripts.data_generator import generate_products, save_products
    
    print("Örnek veriler oluşturuluyor...")
    products = generate_products(300000)
    save_products(products)
    print("Örnek veriler oluşturuldu.")
    
    # Verileri Elasticsearch'e yükle
    print("\nVeriler Elasticsearch'e yükleniyor...")
    success = index_products_from_json()
    
    if success:
        print("\nTüm işlemler başarıyla tamamlandı!")
    else:
        print("\nİşlem sırasında hatalar oluştu!") 