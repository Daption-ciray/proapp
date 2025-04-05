from sqlalchemy import create_engine
from app.database.database import Base
from app.models.user_preferences import UserPreferences, SearchHistory
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    from app.database.database import engine
    
    print("Veritabanı tablolarını oluşturma başlıyor...")
    
    # Drop existing tables
    print("Eski tabloları silme...")
    try:
        SearchHistory.__table__.drop(engine, checkfirst=True)
        UserPreferences.__table__.drop(engine, checkfirst=True)
        print("Eski tablolar silindi.")
    except Exception as e:
        print(f"Tablo silme hatası (önemsiz olabilir): {e}")
    
    # Create tables
    print("Yeni tabloları oluşturma...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tablolar başarıyla oluşturuldu!")
        return True
    except Exception as e:
        print(f"Tablo oluşturma hatası: {e}")
        return False

if __name__ == "__main__":
    create_tables() 