from typing import Dict, Any, Optional, List
import redis
import json
from functools import wraps
from datetime import timedelta

# Redis connection - optional
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=1,  # 1 second timeout
        socket_timeout=1
    )
    # Test connection
    redis_client.ping()
except:
    print("Redis connection failed. Caching will be disabled.")
    redis_client = None

class CacheManager:
    def __init__(self):
        self.cache = redis_client
        self.default_ttl = timedelta(hours=24)

    def get_cache_key(self, query: str, filters: Dict[str, Any]) -> str:
        """Cache key oluştur"""
        cache_key = f"search:{query}"
        if filters:
            # Filtreleri sırala ve cache key'e ekle
            sorted_filters = sorted(filters.items())
            cache_key += f":{json.dumps(sorted_filters)}"
        return cache_key

    def get_cached_results(self, cache_key: str) -> Optional[List[Dict]]:
        """Cache'den sonuçları getir"""
        if not self.cache:
            return None
        try:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Cache okuma hatası: {e}")
        return None

    def set_cached_results(self, cache_key: str, results: List[Dict], ttl: Optional[timedelta] = None) -> None:
        """Sonuçları cache'e kaydet"""
        if not self.cache:
            return
        try:
            ttl = ttl or self.default_ttl
            self.cache.setex(
                cache_key,
                ttl,
                json.dumps(results)
            )
        except Exception as e:
            print(f"Cache yazma hatası: {e}")

def cache_search_results(ttl: Optional[timedelta] = None):
    """Search sonuçlarını cache'leyen decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Cache manager instance
            cache_mgr = CacheManager()
            
            # Redis bağlantısı yoksa direkt fonksiyonu çalıştır
            if not cache_mgr.cache:
                return func(*args, **kwargs)
            
            # Cache key oluştur
            query = kwargs.get('query', '')
            filters = kwargs.get('filters', {})
            cache_key = cache_mgr.get_cache_key(query, filters)
            
            # Cache'den kontrol et
            cached_results = cache_mgr.get_cached_results(cache_key)
            if cached_results is not None:
                print(f"Cache hit for key: {cache_key}")
                return cached_results
            
            # Cache'de yoksa fonksiyonu çalıştır
            results = func(*args, **kwargs)
            
            # Sonuçları cache'e kaydet
            cache_mgr.set_cached_results(cache_key, results, ttl)
            
            return results
        return wrapper
    return decorator 