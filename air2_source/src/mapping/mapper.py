"""Map Generator and Tile Manager"""
import os, math, json
from typing import List, Tuple, Dict, Any, Optional

class MapGenerator:
    def __init__(self, tile_dir: str = './tiles'): self.tile_dir = tile_dir; os.makedirs(tile_dir, exist_ok=True)
    def generate_tile(self, x: int, y: int, zoom: int) -> bytes:
        return b'PNG_DATA'
    def get_tile_path(self, x: int, y: int, zoom: int) -> str:
        return os.path.join(self.tile_dir, f'{zoom}', f'{x}', f'{y}.png')
    def save_tile(self, x: int, y: int, zoom: int, data: bytes) -> bool:
        try:
            p = self.get_tile_path(x, y, zoom); os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'wb') as f: f.write(data); return True
        except: return False
    def load_tile(self, x: int, y: int, zoom: int) -> Optional[bytes]:
        p = self.get_tile_path(x, y, zoom)
        if os.path.exists(p):
            with open(p, 'rb') as f: return f.read()
        return None
    def bounds_to_tiles(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float, zoom: int) -> List[Tuple[int, int]]:
        tiles = []
        min_x, max_x = int(self.lon_to_tile(min_lon, zoom)), int(self.lon_to_tile(max_lon, zoom))
        min_y, max_y = int(self.lat_to_tile(max_lat, zoom)), int(self.lat_to_tile(min_lat, zoom))
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1): tiles.append((x, y))
        return tiles
    def lon_to_tile(self, lon: float, zoom: int) -> float: return (lon + 180.0) / 360.0 * (1 << zoom)
    def lat_to_tile(self, lat: float, zoom: int) -> float: return (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * (1 << zoom)
    def tile_to_lon(self, x: int, zoom: int) -> float: return x / (1 << zoom) * 360.0 - 180.0
    def tile_to_lat(self, y: int, zoom: int) -> float: return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / (1 << zoom)))))
    def export_map(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float, zoom: int, format: str = 'png') -> str:
        tiles = self.bounds_to_tiles(min_lat, min_lon, max_lat, max_lon, zoom)
        out_file = f'map_{zoom}_{min_lat}_{min_lon}.{format}'
        return f'Exported {len(tiles)} tiles to {out_file}'

class TileManager:
    def __init__(self, cache_dir: str = './tile_cache'): self.cache_dir = cache_dir; os.makedirs(cache_dir, exist_ok=True)
    def cache_tile(self, data: bytes, source: str, x: int, y: int, zoom: int) -> str:
        path = os.path.join(self.cache_dir, source, str(zoom), str(x), f'{y}.png')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f: f.write(data)
        return path
    def get_cached(self, source: str, x: int, y: int, zoom: int) -> Optional[bytes]:
        path = os.path.join(self.cache_dir, source, str(zoom), str(x), f'{y}.png')
        if os.path.exists(path):
            with open(path, 'rb') as f: return f.read()
        return None
    def clear_cache(self, source: str = None) -> int:
        count = 0
        if source:
            path = os.path.join(self.cache_dir, source)
            if os.path.exists(path):
                import shutil; shutil.rmtree(path); count = 1
        return count
    def get_cache_size(self) -> int:
        total = 0
        for r, ds, fs in os.walk(self.cache_dir):
            for f in fs: total += os.path.getsize(os.path.join(r, f))
        return total
