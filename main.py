# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Product
from database import SessionLocal, engine
from pydantic import BaseModel

# --------------------------
# Pydantic Modellerini Düzenle
# --------------------------

# Request için model
class PromptRequest(BaseModel):
    prompt: str

# Response için model (Product tablosuyla eşleşmeli)
class ProductResponse(BaseModel):
    product_id: int
    name: str
    category: str
    price: float
    description: str

    class Config:
        orm_mode = True

# --------------------------
# Veritabanı ve Uygulama Ayarları
# --------------------------

Product.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------
# Endpoint'leri Güncelle
# --------------------------

@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    """Tüm ürünleri listeler"""
    return db.query(Product).all()

@app.get("/products/{category}", response_model=list[ProductResponse])
def get_products_by_category(category: str, db: Session = Depends(get_db)):
    """Kategoriye göre filtreleme yapar"""
    products = db.query(Product).filter(Product.category == category).all()
    if not products:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    return products

@app.post("/search", response_model=list[ProductResponse])
def search_products(request: PromptRequest, db: Session = Depends(get_db)):
    """Prompt'a göre ürün önerir"""
    prompt = request.prompt.lower()
    
    # Filtreleme mantığı
    if "teknoloji" in prompt:
        products = db.query(Product).filter(Product.category == "teknoloji").limit(5).all()
    elif "giyim" in prompt:
        products = db.query(Product).filter(Product.category == "giyim").limit(5).all()
    else:
        products = db.query(Product).limit(5).all()
    
    return products