from sqlalchemy.orm import Session
from ..models.product import Product
from ..database.database import SessionLocal, engine, Base
import json

# Örnek ürün verileri
sample_products = [
    {
        "brand": "Nike",
        "model": "Air Max 270",
        "price": 2499.99,
        "category": "Spor Ayakkabı",
        "target_audience": "Erkek",
        "description": "Nike Air Max 270, maksimum konfor için tasarlanmış Air ünitesi ve şık görünümü ile günlük kullanım için ideal bir spor ayakkabı."
    },
    {
        "brand": "Adidas",
        "model": "Ultraboost 21",
        "price": 2799.99,
        "category": "Koşu Ayakkabısı",
        "target_audience": "Unisex",
        "description": "Adidas Ultraboost 21, responsive Boost teknolojisi ve sürdürülebilir malzemelerle üretilen üst kısmı ile maksimum performans sunar."
    },
    {
        "brand": "Puma",
        "model": "RS-X³",
        "price": 1899.99,
        "category": "Günlük Ayakkabı",
        "target_audience": "Unisex",
        "description": "Puma RS-X³, retro running stilini modern detaylarla birleştiren, rahat ve şık bir günlük ayakkabı."
    },
    {
        "brand": "New Balance",
        "model": "574",
        "price": 1599.99,
        "category": "Sneaker",
        "target_audience": "Kadın",
        "description": "New Balance 574, klasik tasarımı ve üstün konforu ile günlük kullanım için mükemmel bir seçim."
    },
    {
        "brand": "Nike",
        "model": "Air Force 1",
        "price": 1899.99,
        "category": "Sneaker",
        "target_audience": "Unisex",
        "description": "Nike Air Force 1, zamansız tasarımı ve dayanıklı yapısı ile sokak stilinin vazgeçilmez parçası."
    },
    {
        "brand": "Adidas",
        "model": "Stan Smith",
        "price": 1699.99,
        "category": "Günlük Ayakkabı",
        "target_audience": "Unisex",
        "description": "Adidas Stan Smith, minimalist tasarımı ve sürdürülebilir malzemeleri ile modern bir klasik."
    },
    {
        "brand": "Asics",
        "model": "Gel-Nimbus 23",
        "price": 2899.99,
        "category": "Koşu Ayakkabısı",
        "target_audience": "Erkek",
        "description": "Asics Gel-Nimbus 23, GEL teknolojisi ve FlyteFoam orta tabanı ile uzun mesafe koşucuları için tasarlandı."
    },
    {
        "brand": "Skechers",
        "model": "D'Lites",
        "price": 899.99,
        "category": "Günlük Ayakkabı",
        "target_audience": "Kadın",
        "description": "Skechers D'Lites, hafif yapısı ve memory foam tabanlığı ile gün boyu konfor sağlar."
    },
    {
        "brand": "Under Armour",
        "model": "HOVR Phantom 2",
        "price": 2299.99,
        "category": "Koşu Ayakkabısı",
        "target_audience": "Erkek",
        "description": "Under Armour HOVR Phantom 2, enerji dönüşünü maksimize eden HOVR teknolojisi ile yüksek performans sunar."
    },
    {
        "brand": "Reebok",
        "model": "Classic Leather",
        "price": 1299.99,
        "category": "Sneaker",
        "target_audience": "Unisex",
        "description": "Reebok Classic Leather, vintage görünümü ve yumuşak deri üst malzemesi ile zamansız bir stil sunar."
    }
]

def seed_database():
    """Veritabanına örnek ürünleri ekle"""
    db = SessionLocal()
    try:
        # Mevcut ürünleri temizle
        db.query(Product).delete()
        
        # Yeni ürünleri ekle
        for product_data in sample_products:
            product = Product(**product_data)
            db.add(product)
        
        db.commit()
        print(f"{len(sample_products)} ürün başarıyla eklendi.")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_database() 