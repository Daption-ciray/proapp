import redis
from typing import Optional, Any
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CacheService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            try:
                # Redis bağlantısını kur
                cls._instance.redis = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=int(os.getenv('REDIS_DB', 0)),
                    decode_responses=True
                )
                # Bağlantıyı test et
                cls._instance.redis.ping()
                print("Redis connection successful")
            except redis.ConnectionError as e:
                print(f"Redis connection failed: {e}")
                cls._instance.redis = None
        return cls._instance

    def get(self, key: str) -> Optional[Any]:
        """Redis'ten veri çek"""
        if not self.redis:
            return None
            
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Redis'e veri kaydet"""
        if not self.redis:
            return False
            
        try:
            self.redis.setex(
                name=key,
                time=expire,
                value=json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Redis'ten veri sil"""
        if not self.redis:
            return False
            
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def clear(self) -> bool:
        """Tüm cache'i temizle"""
        if not self.redis:
            return False
            
        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False 