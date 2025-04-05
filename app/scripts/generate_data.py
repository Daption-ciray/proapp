from faker import Faker
import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.database.database import SessionLocal, engine, Base
from app.models.product import Product

# Faker instance'ı oluştur
fake = Faker(['tr_TR'])

# Markalar - kategorilere göre gruplandırılmış
brands = {
    "Elektronik": [
        "Apple", "Samsung", "Sony", "LG", "Philips", "Asus", "Lenovo", "HP", 
        "Dell", "Huawei", "Xiaomi", "Oppo", "Vivo", "MSI", "Acer", "Toshiba",
        "JBL", "Beats", "Bose", "Monster", "Razer", "Logitech", "Canon", "Nikon"
    ],
    "Giyim": [
        "Nike", "Adidas", "Puma", "Mavi", "Zara", "H&M", "Pull&Bear", "Bershka",
        "Lacoste", "Tommy Hilfiger", "Polo", "Vakko", "Beymen", "Koton", "LC Waikiki",
        "DeFacto", "Pierre Cardin", "US Polo", "Network", "Twist", "Marks & Spencer"
    ],
    "Ev Aletleri": [
        "Beko", "Arçelik", "Vestel", "Bosch", "Siemens", "Dyson", "Tefal",
        "Philips", "Samsung", "LG", "Electrolux", "Profilo", "Grundig", "Fakir",
        "Sinbo", "Arzum", "King", "Braun", "Rowenta", "Fantom"
    ],
    "Mobilya": [
        "IKEA", "Bellona", "İstikbal", "Mondi", "Çilek", "Weltew", "Kelebek",
        "Vivense", "Evidea", "Modalife", "Tepe Home", "Doğtaş", "Alfemo", "Çetmen"
    ],
    "Kozmetik": [
        "MAC", "Maybelline", "L'Oreal", "Nivea", "Clinique", "Estee Lauder",
        "The Body Shop", "NYX", "Urban Decay", "Flormar", "Golden Rose", "Neutrogena",
        "Garnier", "Yves Rocher", "Farmasi", "Avon", "Oriflame"
    ]
}

# Gelir grupları ve fiyat aralıkları
income_groups = {
    "Ekonomik": {
        "price_range": (10, 1000),
        "brands": ["DeFacto", "LC Waikiki", "Sinbo", "Fantom", "Flormar", "Golden Rose"]
    },
    "Orta Segment": {
        "price_range": (1000, 5000),
        "brands": ["Mavi", "Koton", "Beko", "Vestel", "Philips", "Arzum"]
    },
    "Üst Segment": {
        "price_range": (5000, 15000),
        "brands": ["Tommy Hilfiger", "Lacoste", "Dyson", "Bosch", "Samsung", "Apple"]
    },
    "Premium": {
        "price_range": (15000, 50000),
        "brands": ["Vakko", "Beymen", "Apple", "Bose", "Miele", "Bang & Olufsen"]
    },
    "Lüks": {
        "price_range": (50000, 200000),
        "brands": ["Rolex", "Louis Vuitton", "Gucci", "Prada", "Cartier", "Hermès"]
    }
}

categories = [
    "Elektronik", "Giyim", "Ev Aletleri", "Mobilya", "Kozmetik",
    "Spor", "Kitap", "Oyuncak", "Bahçe", "Otomotiv", "Aksesuar",
    "Gıda", "Kırtasiye", "Sağlık", "Hobi", "Mücevher", "Saat",
    "Çanta", "Ayakkabı", "Outdoor", "Yapı Market", "Pet Shop"
]

target_audiences = [
    "Erkek", "Kadın", "Unisex", "Çocuk", "Genç", "Yetişkin", 
    "Yaşlı", "Aile", "Profesyonel", "Öğrenci", "Sporcu", "İş İnsanı",
    "Ev Hanımı", "Bebek", "Hamile", "Emekli"
]

# Kategori bazlı ürün özellikleri ve açıklamaları
category_details = {
    "Elektronik": {
        "features": [
            "Yüksek performanslı işlemci", "Geniş ekran", "Uzun pil ömrü",
            "Hızlı şarj desteği", "Kablosuz bağlantı", "Akıllı sensörler",
            "Yüksek çözünürlük", "Gelişmiş soğutma sistemi", "Kompakt tasarım",
            "Gürültü önleme teknolojisi", "5G desteği", "Wi-Fi 6 uyumlu",
            "Yapay zeka destekli", "Hızlı şarj özelliği", "Su ve toz direnci"
        ],
        "desc_template": "{model}, {feature1} ile donatılmış {brand} kalitesiyle üretilmiştir. {feature2} özelliği sayesinde maksimum performans sunar. {feature3} teknolojisiyle kullanıcı deneyimini üst seviyeye taşır. {target_audience} kullanıcılar için {income_group} segmentinde ideal bir üründür."
    },
    "Giyim": {
        "features": [
            "Premium kumaş", "Nefes alabilen materyal", "Esnek yapı", 
            "Modern kesim", "Rahat kalıp", "Özel dokuma", "Mevsimlik tasarım",
            "Şık detaylar", "Kolay bakım", "Leke tutmaz", "Anti-bakteriyel",
            "UV koruma", "Ter emici", "Hızlı kuruyan", "Dayanıklı dikiş"
        ],
        "desc_template": "{brand} imzalı {model}, {feature1} kullanılarak üretilmiştir. {feature2} sayesinde maksimum konfor sağlar. {feature3} özelliğiyle öne çıkan ürün, {target_audience} için {income_group} segmentinde özel olarak tasarlanmıştır."
    }
}

# Diğer kategoriler için varsayılan şablon
default_features = [
    "Yüksek kalite", "Modern tasarım", "Dayanıklı yapı",
    "Kullanıcı dostu", "Özel üretim", "Premium malzeme",
    "Şık görünüm", "Pratik kullanım", "Uzun ömürlü",
    "Ergonomik yapı"
]

default_template = "{brand} {model}, {feature1} ile öne çıkan bir üründür. {feature2} özelliği ile kullanıcılardan tam not alır. {feature3} yapısıyla uzun yıllar kullanım sunar. {target_audience} için özel olarak tasarlanmıştır."

def generate_price_by_income_group(brand):
    for group, details in income_groups.items():
        if brand in details["brands"]:
            min_price, max_price = details["price_range"]
            return round(random.uniform(min_price, max_price), 2)
    
    # Eğer marka belirli bir gelir grubunda değilse orta segment fiyat ver
    return round(random.uniform(1000, 5000), 2)

def get_income_group(price):
    for group, details in income_groups.items():
        min_price, max_price = details["price_range"]
        if min_price <= price <= max_price:
            return group
    return "Orta Segment"

def generate_description(brand, model, category, target_audience, price):
    income_group = get_income_group(price)
    category_info = category_details.get(category, {"features": default_features, "desc_template": default_template})
    
    selected_features = random.sample(category_info["features"], 3)
    
    return category_info["desc_template"].format(
        brand=brand,
        model=model,
        feature1=selected_features[0],
        feature2=selected_features[1],
        feature3=selected_features[2],
        target_audience=target_audience,
        income_group=income_group
    )

def generate_products(db, count=5000):
    products = []
    for _ in range(count):
        category = random.choice(categories)
        brand = random.choice(brands.get(category, list(brands.values())[0]))
        model = f"{fake.word().capitalize()} {random.randint(1000, 9999)}"
        target_audience = random.choice(target_audiences)
        price = generate_price_by_income_group(brand)
        
        product = Product(
            brand=brand,
            price=price,
            category=category,
            model=model,
            target_audience=target_audience,
            description=generate_description(brand, model, category, target_audience, price)
        )
        products.append(product)
    
    db.bulk_save_objects(products)
    db.commit()

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Önce mevcut verileri temizle
    db.query(Product).delete()
    db.commit()
    
    # Yeni verileri oluştur
    generate_products(db)
    db.close()

if __name__ == "__main__":
    main() 