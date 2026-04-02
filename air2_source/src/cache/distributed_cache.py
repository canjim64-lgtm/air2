"""
Caching Module
Distributed caching system can
"""

import time
from typing import Any, Optional


class Cache:
    """In-memory cache"""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.store = {}
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set cache"""
        self.store[key] = {
            'value': value,
            'expires': time.time() + (ttl or self.ttl)
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache"""
        if key in self.store:
            item = self.store[key]
            if time.time() < item['expires']:
                return item['value']
            del self.store[key]
        return None
    
    def delete(self, key: str):
        """Delete cache"""
        if key in self.store:
            del self.store[key]
    
    def clear(self):
        """Clear cache"""
        self.store.clear()


class RedisCache:
    """Redis cache (simulated)"""
    
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.host = host
        self.port = port
        self.cache = {}
    
    def set(self, key: str, value: str, ex: int = None):
        """Set cache"""
        self.cache[key] = value
    
    def get(self, key: str) -> Optional[str]:
        """Get cache"""
        return self.cache.get(key)
    
    def delete(self, key: str):
        """Delete"""
        if key in self.cache:
            del self.cache[key]


# Example
if __name__ == "__main__":
    cache = Cache()
    cache.set("test", "value")
    print(f"Get: {cache.get('test')}")
