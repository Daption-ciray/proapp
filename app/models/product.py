from sqlalchemy import Column, Integer, String, Float, Text
from ..database.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(100), index=True)
    price = Column(Float)
    category = Column(String(100), index=True)
    model = Column(String(200))
    target_audience = Column(String(100))
    description = Column(Text) 