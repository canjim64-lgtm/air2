#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Advanced Caching System
Multi-level caching with memory, disk, and distributed cache support
"""

import os
import sys
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
import logging
import pickle
from functools import wraps
from collections import OrderedDict


class CacheEntry:
    """Represents a cache entry"""
    
    def __init__(self, key: str, value: Any, ttl: int = None):
        self.key = key
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl = ttl  # Time to live in seconds
        if ttl:
            self.expires_at = self.created_at + timedelta(seconds=ttl)
        else:
            self.expires_at = None
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def access(self):
        """Record access"""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat()
        }


class MemoryCache:
    """In-memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired():
                    del self.cache[key]
                    self.misses += 1
                    return None
                entry.access()
                self.cache.move_to_end(key)
                self.hits += 1
                return entry.value
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            elif len(self.cache) >= self.max_size:
                # Remove oldest entry
                self.cache.popitem(last=False)
            
            entry = CacheEntry(key, value, ttl)
            self.cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0
            return {
                'type': 'memory',
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_percent': round(hit_rate, 2)
            }


class DiskCache:
    """Disk-based cache for persistence"""
    
    def __init__(self, cache_dir: str = None, max_size_mb: float = 100.0):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / 'data' / 'cache' / 'disk'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.index_file = self.cache_dir / 'index.json'
        self.index = {}
        self.lock = threading.RLock()
        self._load_index()
    
    def _load_index(self):
        """Load cache index"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except:
                self.index = {}
    
    def _save_index(self):
        """Save cache index"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f'{key_hash}.cache'
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.index:
                return None
            
            entry = self.index[key]
            created_at = datetime.fromisoformat(entry['created_at'])
            
            # Check expiration
            if entry.get('ttl'):
                expires_at = created_at + timedelta(seconds=entry['ttl'])
                if datetime.utcnow() > expires_at:
                    self.delete(key)
                    return None
            
            # Read from disk
            file_path = self._get_file_path(key)
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)
                    entry['access_count'] = entry.get('access_count', 0) + 1
                    entry['last_accessed'] = datetime.utcnow().isoformat()
                    self._save_index()
                    return data
                except:
                    return None
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache"""
        with self.lock:
            file_path = self._get_file_path(key)
            
            # Check disk space
            current_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.cache'))
            if current_size >= self.max_size_bytes:
                # Cleanup old entries
                self._cleanup()
            
            # Write to disk
            try:
                with open(file_path, 'wb') as f:
                    pickle.dump(value, f)
                
                self.index[key] = {
                    'file': str(file_path),
                    'created_at': datetime.utcnow().isoformat(),
                    'ttl': ttl,
                    'size': file_path.stat().st_size,
                    'access_count': 0,
                    'last_accessed': datetime.utcnow().isoformat()
                }
                self._save_index()
            except Exception as e:
                logging.error(f"Disk cache set error: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self.lock:
            if key in self.index:
                file_path = self._get_file_path(key)
                if file_path.exists():
                    file_path.unlink()
                del self.index[key]
                self._save_index()
                return True
            return False
    
    def _cleanup(self):
        """Cleanup old cache entries"""
        # Remove oldest entries until under size limit
        sorted_entries = sorted(
            self.index.items(),
            key=lambda x: x[1].get('last_accessed', '')
        )
        
        current_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.cache'))
        
        for key, _ in sorted_entries:
            if current_size < self.max_size_bytes:
                break
            self.delete(key)
            current_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.cache'))
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            for f in self.cache_dir.glob('*.cache'):
                f.unlink()
            self.index = {}
            self._save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.cache'))
            return {
                'type': 'disk',
                'size': len(self.index),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'max_size_mb': round(self.max_size_bytes / (1024 * 1024), 2)
            }


class CacheManager:
    """Multi-level cache manager"""
    
    def __init__(self, memory_max_size: int = 1000, disk_max_size_mb: float = 100.0):
        self.memory_cache = MemoryCache(memory_max_size)
        self.disk_cache = DiskCache(disk_max_size_mb)
        self.lock = threading.RLock()
        self.enabled = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (memory first, then disk)"""
        if not self.enabled:
            return default
        
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try disk cache
        value = self.disk_cache.get(key)
        if value is not None:
            # Promote to memory cache
            self.memory_cache.set(key, value)
            return value
        
        return default
    
    def set(self, key: str, value: Any, ttl: int = None, level: str = 'both'):
        """Set value in cache"""
        if not self.enabled:
            return
        
        with self.lock:
            if level in ['memory', 'both']:
                self.memory_cache.set(key, value, ttl)
            
            if level in ['disk', 'both']:
                self.disk_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """Delete value from cache"""
        with self.lock:
            self.memory_cache.delete(key)
            self.disk_cache.delete(key)
    
    def clear(self, level: str = 'both'):
        """Clear cache"""
        with self.lock:
            if level in ['memory', 'both']:
                self.memory_cache.clear()
            
            if level in ['disk', 'both']:
                self.disk_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'enabled': self.enabled,
            'memory': self.memory_cache.get_stats(),
            'disk': self.disk_cache.get_stats()
        }
    
    def enable(self):
        """Enable caching"""
        self.enabled = True
    
    def disable(self):
        """Disable caching"""
        self.enabled = False


def cached(ttl: int = None, level: str = 'both'):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache manager from function module or create one
            cache_manager = getattr(func, '_cache_manager', None)
            if not cache_manager:
                return func(*args, **kwargs)
            
            # Generate cache key
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = cache_manager.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl, level)
            return result
        
        return wrapper
    return decorator


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def initialize_cache(memory_max_size: int = 1000, disk_max_size_mb: float = 100.0) -> CacheManager:
    """Initialize global cache manager"""
    global _cache_manager
    _cache_manager = CacheManager(memory_max_size, disk_max_size_mb)
    return _cache_manager


if __name__ == '__main__':
    # Test cache system
    logging.basicConfig(level=logging.INFO)
    
    cache = initialize_cache()
    
    # Test memory cache
    cache.set('test_key', 'test_value', ttl=60)
    value = cache.get('test_key')
    print(f"Cache value: {value}")
    
    # Test stats
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # Test decorator
    @cached(ttl=300)
    def expensive_operation(x, y):
        time.sleep(1)  # Simulate expensive operation
        return x + y
    
    # Attach cache manager to function
    expensive_operation._cache_manager = cache
    
    result = expensive_operation(5, 3)
    print(f"Operation result: {result}")
    
    print("Cache system tests completed")
