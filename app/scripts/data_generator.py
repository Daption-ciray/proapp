from faker import Faker
import random
from datetime import datetime, timedelta
import json
from typing import List, Dict
import numpy as np

fake = Faker(['tr_TR'])

# Kategori yapısı
CATEGORIES = {
    "Elektronik": {
        "subcategories": {
            "Akıllı Telefonlar": ["Apple", "Samsung", "Xiaomi", "Huawei", "OPPO", "Vivo", "realme", "OnePlus"],
            "Laptoplar": ["Apple", "ASUS", "Lenovo", "HP", "Dell", "MSI", "Monster", "Casper"],
            "Tabletler": ["Apple", "Samsung", "Lenovo", "Huawei", "Xiaomi"],
            "Akıllı Saatler": ["Apple", "Samsung", "Huawei", "Xiaomi", "Garmin"],
            "Kulaklıklar": ["Apple", "Samsung", "JBL", "Sony", "Xiaomi", "Huawei"],
            "TV": ["Samsung", "LG", "Sony", "Philips", "TCL", "Vestel"],
            "Oyun Konsolları": ["Sony", "Microsoft", "Nintendo"],
            "Kameralar": ["Canon", "Nikon", "Sony", "Fujifilm"]
        },
        "price_range": (1000, 50000)
    },
    "Moda": {
        "subcategories": {
            "Ayakkabı": ["Nike", "Adidas", "Puma", "New Balance", "Skechers", "Under Armour", "ASICS", "Reebok"],
            "Spor Giyim": ["Nike", "Adidas", "Puma", "Under Armour", "New Balance", "Reebok"],
            "Günlük Giyim": ["Zara", "H&M", "Mavi", "LCW", "Pull&Bear", "Bershka"],
            "İş Giyim": ["Hugo Boss", "Altınyıldız", "Kiğılı", "Ramsey", "Network"],
            "Çanta": ["Michael Kors", "Coach", "Nike", "Adidas", "Guess"],
            "Aksesuar": ["Swatch", "Fossil", "Ray-Ban", "Daniel Wellington"]
        },
        "price_range": (50, 5000)
    },
    "Ev & Yaşam": {
        "subcategories": {
            "Mobilya": ["IKEA", "Bellona", "İstikbal", "Mondi", "Çilek"],
            "Beyaz Eşya": ["Arçelik", "Beko", "Bosch", "Siemens", "Samsung", "LG"],
            "Küçük Ev Aletleri": ["Arzum", "Philips", "Bosch", "Siemens", "Tefal"],
            "Ev Tekstili": ["English Home", "Madame Coco", "Taç", "Yataş"],
            "Mutfak Gereçleri": ["Karaca", "Bernardo", "Paşabahçe", "Keramika"]
        },
        "price_range": (100, 30000)
    },
    "Kitap & Hobi": {
        "subcategories": {
            "Kitaplar": ["Yapı Kredi Yayınları", "İş Bankası Kültür", "Can Yayınları", "Doğan Kitap"],
            "Oyuncaklar": ["LEGO", "Barbie", "Hot Wheels", "Fisher-Price"],
            "Müzik Aletleri": ["Yamaha", "Roland", "Casio", "Kawai"],
            "Sanat Malzemeleri": ["Faber-Castell", "Staedtler", "Artline", "Derwent"]
        },
        "price_range": (20, 10000)
    },
    "Spor & Outdoor": {
        "subcategories": {
            "Fitness Ekipmanları": ["Technogym", "Life Fitness", "Precor", "Matrix"],
            "Kamp Malzemeleri": ["The North Face", "Columbia", "Jack Wolfskin", "Quechua"],
            "Bisikletler": ["Bianchi", "Salcano", "Kron", "Ghost"],
            "Su Sporları": ["Speedo", "Arena", "TYR", "Aqua Sphere"]
        },
        "price_range": (100, 20000)
    }
}

# Hedef kitle seçenekleri
TARGET_AUDIENCES = ["Erkek", "Kadın", "Unisex", "Çocuk", "Genç", "Yetişkin"]

def generate_description(category: str, subcategory: str, brand: str, model: str) -> str:
    """Ürün için gerçekçi açıklama oluştur"""
    features = {
        "Elektronik": [
            "yüksek performanslı", "enerji verimli", "akıllı", "yenilikçi", "kompakt",
            "kullanıcı dostu", "dayanıklı", "premium", "profesyonel", "taşınabilir"
        ],
        "Moda": [
            "şık", "rahat", "modern", "klasik", "sportif", "zarif", "dayanıklı",
            "hafif", "nefes alabilen", "su geçirmez"
        ],
        "Ev & Yaşam": [
            "fonksiyonel", "şık", "dayanıklı", "modern", "ergonomik", "pratik",
            "enerji tasarruflu", "kompakt", "çok amaçlı", "dekoratif"
        ],
        "Kitap & Hobi": [
            "eğitici", "eğlenceli", "yaratıcı", "ilham verici", "kaliteli",
            "profesyonel", "başlangıç seviyesi", "gelişmiş", "popüler", "klasik"
        ],
        "Spor & Outdoor": [
            "profesyonel", "dayanıklı", "hafif", "su geçirmez", "nefes alabilen",
            "ergonomik", "yüksek performanslı", "kompakt", "çok yönlü", "güvenli"
        ]
    }
    
    category_features = features.get(category, features["Elektronik"])
    selected_features = random.sample(category_features, 3)
    
    templates = [
        f"{brand} {model}, {', '.join(selected_features)} özellikleriyle öne çıkan bir üründür.",
        f"Bu {subcategory.lower()}, {selected_features[0]} tasarımı ve {selected_features[1]} yapısıyla dikkat çeker.",
        f"{brand}'ın en yeni {subcategory.lower()} modeli {model}, {selected_features[0]} ve {selected_features[1]} özellikleriyle kullanıcıların beğenisini kazanıyor.",
        f"Yenilikçi özellikleriyle öne çıkan {brand} {model}, {selected_features[0]} yapısı ve {selected_features[1]} tasarımıyla {subcategory.lower()} kategorisinde fark yaratıyor."
    ]
    
    return random.choice(templates)

def generate_model_name() -> str:
    """Gerçekçi model ismi oluştur"""
    model_types = [
        lambda: f"{random.choice(['Pro', 'Lite', 'Plus', 'Max', 'Ultra'])}-{fake.random_int(min=1000, max=9999)}",
        lambda: f"{fake.random_letter().upper()}{fake.random_int(min=10, max=99)}{random.choice(['X', 'S', 'E', 'T'])}",
        lambda: f"{random.choice(['Neo', 'Air', 'Smart', 'Elite'])}-{fake.random_int(min=100, max=999)}",
        lambda: f"{datetime.now().year}-{fake.random_letter().upper()}{fake.random_int(min=10, max=99)}",
    ]
    return random.choice(model_types)()

def generate_price(base_range: tuple) -> float:
    """Gerçekçi fiyat oluştur"""
    min_price, max_price = base_range
    # Log-normal dağılım kullanarak daha gerçekçi fiyat dağılımı oluştur
    mu = np.log((min_price + max_price) / 2)
    sigma = 0.5
    price = np.random.lognormal(mu, sigma)
    # Fiyatı belirlenen aralığa sınırla
    price = max(min_price, min(max_price, price))
    # Kuruş hassasiyetine yuvarla
    return round(price, 2)

def generate_products(count: int = 300000) -> List[Dict]:
    """Belirtilen sayıda ürün oluştur"""
    products = []
    
    for _ in range(count):
        # Rastgele kategori ve alt kategori seç
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(list(CATEGORIES[category]["subcategories"].keys()))
        brand = random.choice(CATEGORIES[category]["subcategories"][subcategory])
        
        # Ürün oluştur
        product = {
            "brand": brand,
            "model": generate_model_name(),
            "price": generate_price(CATEGORIES[category]["price_range"]),
            "category": subcategory,
            "target_audience": random.choice(TARGET_AUDIENCES),
            "description": None  # Geçici olarak None atanır
        }
        
        # Açıklama oluştur
        product["description"] = generate_description(
            category, subcategory, product["brand"], product["model"]
        )
        
        products.append(product)
    
    return products

def save_products(products: List[Dict], filename: str = "products.json"):
    """Ürünleri JSON dosyasına kaydet"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("Ürünler oluşturuluyor...")
    products = generate_products()
    print(f"{len(products)} ürün oluşturuldu.")
    
    print("Ürünler JSON dosyasına kaydediliyor...")
    save_products(products)
    print("İşlem tamamlandı.") 