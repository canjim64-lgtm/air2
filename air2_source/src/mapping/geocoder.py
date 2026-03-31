"""Geocoding and Reverse Geocoding"""
import json, math
from typing import Dict, List, Any, Optional, Tuple

class Geocoder:
    def __init__(self, cache_file: str = './geocode_cache.json'): self.cache_file = cache_file; self.cache = self._load_cache()
    def _load_cache(self) -> Dict: return json.load(open(self.cache_file)) if os.path.exists(self.cache_file) else {}
    def _save_cache(self): json.dump(self.cache, open(self.cache_file, 'w'))
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        if address in self.cache: return self.cache[address]
        return None
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        key = f'{lat:.4f},{lon:.4f}'
        if key in self.cache: return self.cache[key]
        return {'address': f'{lat:.4f}, {lon:.4f}', 'city': 'Unknown', 'country': 'Unknown'}
    def add_to_cache(self, address: str, lat: float, lon: float): self.cache[address] = (lat, lon); self._save_cache()
    def batch_geocode(self, addresses: List[str]) -> Dict[str, Optional[Tuple[float, float]]]:
        return {addr: self.geocode(addr) for addr in addresses}

import os
