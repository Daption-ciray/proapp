from app.database.database import SessionLocal
from app.models.user_preferences import UserPreferences, SearchHistory
import datetime

def create_test_users():
    db = SessionLocal()
    try:
        # İlk kullanıcı - Spor giyim odaklı
        user1 = UserPreferences(
            user_id="user1",
            favorite_categories=["Spor Ayakkabı", "Spor Giyim", "Fitness Ekipmanları"],
            preferred_brands=["Nike", "Adidas", "Under Armour"],
            price_range={"min": 500, "max": 2000}
        )
        db.add(user1)

        # User1 için arama geçmişi
        search_history1 = [
            SearchHistory(
                user_id="user1",
                query="spor ayakkabı",
                filters={"max_price": 1500, "brand": "Nike"},
                results_count=12
            ),
            SearchHistory(
                user_id="user1",
                query="koşu şortu",
                filters={"category": "Spor Giyim"},
                results_count=8
            ),
            SearchHistory(
                user_id="user1",
                query="fitness eldiveni",
                filters={"category": "Fitness Ekipmanları"},
                results_count=5
            )
        ]
        for history in search_history1:
            db.add(history)

        # İkinci kullanıcı - Teknoloji odaklı
        user2 = UserPreferences(
            user_id="user2",
            favorite_categories=["Laptop", "Akıllı Telefon", "Tablet"],
            preferred_brands=["Apple", "Samsung", "Lenovo"],
            price_range={"min": 5000, "max": 25000}
        )
        db.add(user2)

        # User2 için arama geçmişi
        search_history2 = [
            SearchHistory(
                user_id="user2",
                query="macbook pro",
                filters={"category": "Laptop", "brand": "Apple"},
                results_count=6
            ),
            SearchHistory(
                user_id="user2",
                query="galaxy s23",
                filters={"category": "Akıllı Telefon", "brand": "Samsung"},
                results_count=3
            ),
            SearchHistory(
                user_id="user2",
                query="ipad pro",
                filters={"category": "Tablet", "max_price": 20000},
                results_count=4
            )
        ]
        for history in search_history2:
            db.add(history)

        db.commit()
        print("Test kullanıcıları başarıyla oluşturuldu!")

    except Exception as e:
        print(f"Hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users() 