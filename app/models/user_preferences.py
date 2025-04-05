from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database.database import Base
import datetime
from typing import List, Dict, Any

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    favorite_categories = Column(JSON, default=list)
    preferred_brands = Column(JSON, default=list)
    price_range = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    query = Column(String)
    filters = Column(JSON)
    results_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UserPreferencesManager:
    def __init__(self, db_session):
        self.db = db_session

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Kullanıcı tercihlerini getir"""
        prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        if not prefs:
            # Yeni kullanıcı için varsayılan tercihler oluştur
            prefs = UserPreferences(
                user_id=user_id,
                favorite_categories=[],
                preferred_brands=[],
                price_range={"min": None, "max": None}
            )
            self.db.add(prefs)
            self.db.commit()
            self.db.refresh(prefs)
        
        return {
            "favorite_categories": prefs.favorite_categories,
            "preferred_brands": prefs.preferred_brands,
            "price_range": prefs.price_range
        }

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Kullanıcı tercihlerini güncelle"""
        try:
            prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
            if not prefs:
                prefs = UserPreferences(user_id=user_id)
                self.db.add(prefs)

            # Tercihleri güncelle
            if "favorite_categories" in preferences:
                prefs.favorite_categories = preferences["favorite_categories"]
            if "preferred_brands" in preferences:
                prefs.preferred_brands = preferences["preferred_brands"]
            if "price_range" in preferences:
                prefs.price_range = preferences["price_range"]

            self.db.commit()
            return True
        except Exception as e:
            print(f"Tercih güncelleme hatası: {e}")
            return False

    def add_search_history(self, user_id: str, query: str, filters: Dict[str, Any], results_count: int) -> bool:
        """Arama geçmişine yeni kayıt ekle"""
        try:
            history = SearchHistory(
                user_id=user_id,
                query=query,
                filters=filters,
                results_count=results_count
            )
            self.db.add(history)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Arama geçmişi kayıt hatası: {e}")
            return False

    def get_recent_searches(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Kullanıcının son aramalarını getir"""
        searches = self.db.query(SearchHistory)\
            .filter(SearchHistory.user_id == user_id)\
            .order_by(SearchHistory.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [{
            "query": search.query,
            "filters": search.filters,
            "results_count": search.results_count,
            "created_at": search.created_at.isoformat()
        } for search in searches]

    def analyze_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Kullanıcı tercihlerini analiz et"""
        searches = self.db.query(SearchHistory)\
            .filter(SearchHistory.user_id == user_id)\
            .order_by(SearchHistory.created_at.desc())\
            .limit(100)\
            .all()

        # Kategori ve marka tercihlerini analiz et
        categories = {}
        brands = {}
        price_ranges = []

        for search in searches:
            # Kategori analizi
            if search.filters.get("category"):
                cat = search.filters["category"]
                categories[cat] = categories.get(cat, 0) + 1

            # Marka analizi
            if search.filters.get("brand"):
                brand = search.filters["brand"]
                brands[brand] = brands.get(brand, 0) + 1

            # Fiyat aralığı analizi
            if search.filters.get("min_price") or search.filters.get("max_price"):
                price_ranges.append({
                    "min": search.filters.get("min_price"),
                    "max": search.filters.get("max_price")
                })

        # En çok aranan kategoriler ve markalar
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        top_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:5]

        # Ortalama fiyat aralığı
        avg_min = sum(p["min"] for p in price_ranges if p["min"]) / len(price_ranges) if price_ranges else None
        avg_max = sum(p["max"] for p in price_ranges if p["max"]) / len(price_ranges) if price_ranges else None

        return {
            "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
            "top_brands": [{"brand": brand, "count": count} for brand, count in top_brands],
            "average_price_range": {
                "min": round(avg_min, 2) if avg_min else None,
                "max": round(avg_max, 2) if avg_max else None
            }
        } 