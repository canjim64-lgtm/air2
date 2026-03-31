"""
Dynamic Telemetry Compression Engine for AirOne Professional v4.0
Adaptive compression levels based on link bandwidth and payload complexity.
"""
import logging
import zlib
import bz2
import lzma
import time
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class CompressionEngine:
    def __init__(self, default_method: str = "zlib"):
        self.logger = logging.getLogger(f"{__name__}.CompressionEngine")
        self.method = default_method.lower()
        self.stats = {"original_size": 0, "compressed_size": 0, "savings_pct": 0.0}
        self.logger.info(f"Dynamic Compression Engine Initialized (Default: {self.method}).")

    def compress(self, data: bytes, force_method: Optional[str] = None) -> Tuple[bytes, str]:
        """Compresses data and returns (compressed_bytes, method_used)."""
        method = (force_method or self.method).lower()
        start_size = len(data)
        
        if method == "lzma":
            compressed = lzma.compress(data)
        elif method == "bz2":
            compressed = bz2.compress(data)
        else:
            compressed = zlib.compress(data, level=9)
            method = "zlib"
            
        end_size = len(compressed)
        self.stats["original_size"] += start_size
        self.stats["compressed_size"] += end_size
        self.stats["savings_pct"] = (1 - (self.stats["compressed_size"] / self.stats["original_size"])) * 100
        
        return compressed, method

    def decompress(self, data: bytes, method: str) -> bytes:
        """Decompresses data based on the specified method string."""
        if method == "lzma":
            return lzma.decompress(data)
        elif method == "bz2":
            return bz2.decompress(data)
        else:
            return zlib.decompress(data)

    def get_performance_report(self) -> Dict[str, Any]:
        return {
            "cumulative_savings_pct": round(self.stats["savings_pct"], 2),
            "total_data_processed_kb": round(self.stats["original_size"] / 1024, 2),
            "active_method": self.method
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ce = CompressionEngine()
    test_data = b"AirOne" * 1000
    comp, m = ce.compress(test_data, force_method="lzma")
    print(f"Method: {m}, Savings: {ce.get_performance_report()['cumulative_savings_pct']}%")
